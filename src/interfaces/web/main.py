"""Web UI backend for TraderClaw.

Provides REST API and WebSocket endpoints for the single-screen dashboard.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import sys
import asyncio
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.strategies import (
    StrategyExecutionEngine,
    PlainLanguageStrategy,
    StrategyRepository,
    ApprovalMode,
    get_execution_engine,
)
from src.ai.orchestrator import PositionService
from src.infrastructure.brokers import get_broker_manager
from src.ai import StrategyModel

app = FastAPI(title="TraderClaw Web UI", version="1.0.0")

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models
# ============================================================================

class Position(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    portfolio_weight: float
    strategy: Optional[Dict[str, Any]] = None


class Portfolio(BaseModel):
    total_value: float
    cash: float
    positions: List[Position]
    daily_change: float
    daily_change_pct: float


class StrategyInput(BaseModel):
    description: str
    symbol: Optional[str] = None  # If None, applies to whole portfolio
    approval_mode: str = "hybrid"


class StrategyPreview(BaseModel):
    title: str
    interpretation: str
    ambiguities: List[Dict[str, Any]]
    impact: Dict[str, Any]
    confidence: float
    readable_rules: List[str]


class StrategyCreateRequest(BaseModel):
    description: str
    symbol: Optional[str] = None
    approval_mode: str = "hybrid"
    clarifications: Optional[Dict[str, str]] = None


class Alert(BaseModel):
    id: str
    type: str  # "approaching_target", "signal_pending", "risk_alert"
    symbol: str
    message: str
    severity: str  # "info", "warning", "action_required"
    data: Dict[str, Any]
    created_at: datetime


class Signal(BaseModel):
    id: str
    symbol: str
    action: str
    quantity: Optional[float]
    price: Optional[float]
    reason: str
    confidence: float
    position_context: Dict[str, Any]
    portfolio_impact: Dict[str, Any]
    status: str  # "pending", "approved", "rejected", "executed"
    created_at: datetime


class ChatMessage(BaseModel):
    role: str  # "user", "assistant"
    content: str
    timestamp: datetime
    actions: Optional[List[Dict[str, Any]]] = None


# ============================================================================
# Global State (simplified - use proper DB in production)
# ============================================================================

class AppState:
    def __init__(self):
        self.position_service = PositionService()
        self.strategy_repo = StrategyRepository()
        self.broker_manager = get_broker_manager()
        self.strategies: Dict[str, PlainLanguageStrategy] = {}
        self.signals: List[Signal] = []
        self.alerts: List[Alert] = []
        self.chat_history: List[ChatMessage] = []
        self.connected_websockets: List[WebSocket] = []

    def get_portfolio(self) -> Portfolio:
        """Get current portfolio state."""
        # Try to get user context (includes demo data if no CSV loaded)
        import asyncio
        try:
            # Try to get existing CSV positions first
            user_context = asyncio.run(self.position_service.get_user_context("default"))
        except:
            # Fall back to demo context
            user_context = self.position_service._get_demo_context("default")

        if not user_context or not user_context.get("positions"):
            # Return empty portfolio
            return Portfolio(
                total_value=0.0,
                cash=0.0,
                positions=[],
                daily_change=0.0,
                daily_change_pct=0.0,
            )

        positions = []
        total_value = user_context.get("total_portfolio_value", 0)
        cash = user_context.get("cash_available", total_value * 0.1)  # Default 10% cash

        for symbol, pos_data in user_context.get("positions", {}).items():
            quantity = pos_data.get("quantity", 0)
            avg_cost = pos_data.get("avg_entry_price", 0) or pos_data.get("avg_cost", 0)
            current_price = pos_data.get("current_price") or pos_data.get("market_value", 0) / quantity if quantity else 0
            market_value = pos_data.get("market_value", quantity * current_price) if quantity else 0
            unrealized_pnl_pct = pos_data.get("unrealized_pnl_pct", 0) / 100 if pos_data.get("unrealized_pnl_pct") else 0

            positions.append(
                Position(
                    symbol=symbol,
                    quantity=float(quantity),
                    avg_cost=float(avg_cost),
                    current_price=float(current_price),
                    market_value=float(market_value),
                    unrealized_pnl=float(market_value) - (float(quantity) * float(avg_cost)),
                    unrealized_pnl_pct=unrealized_pnl_pct,
                    portfolio_weight=(float(market_value) / total_value) if total_value > 0 else 0,
                    strategy=self._get_strategy_for_symbol(symbol),
                )
            )

        return Portfolio(
            total_value=float(total_value),
            cash=float(cash),
            positions=positions,
            daily_change=0.0,  # Would calculate from historical data
            daily_change_pct=0.0,
        )

    def _get_strategy_for_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get active strategy for a symbol."""
        for strategy in self.strategies.values():
            if symbol in strategy.symbols:
                return {
                    "id": strategy.id,
                    "name": strategy.name,
                    "description": strategy.description[:50] + "...",
                    "approval_mode": strategy.approval_mode.value,
                    "status": "active" if strategy.enabled else "paused",
                }
        return None

    async def broadcast_update(self, message: dict):
        """Broadcast update to all connected WebSocket clients."""
        disconnected = []
        for ws in self.connected_websockets:
            try:
                await ws.send_json(message)
            except:
                disconnected.append(ws)

        for ws in disconnected:
            self.connected_websockets.remove(ws)


state = AppState()


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/portfolio", response_model=Portfolio)
async def get_portfolio():
    """Get current portfolio with positions and strategies."""
    return state.get_portfolio()


@app.post("/api/portfolio/import", response_model=Portfolio)
async def import_portfolio(file_path: str):
    """Import portfolio from CSV file."""
    try:
        positions_data = state.position_service.load_from_csv(file_path)
        return state.get_portfolio()
    except Exception as e:
        raise HTTPException(400, f"Failed to import: {str(e)}")


@app.get("/api/positions/{symbol}/suggestions")
async def get_position_suggestions(symbol: str):
    """Get AI strategy suggestions for a specific position."""
    portfolio = state.get_portfolio()
    position = next((p for p in portfolio.positions if p.symbol == symbol), None)

    if not position:
        raise HTTPException(404, f"Position not found: {symbol}")

    # Generate suggestions based on position state
    suggestions = []

    if position.unrealized_pnl_pct > 0.20:
        suggestions.append({
            "id": "take_profits",
            "title": "🎯 Take Some Profits",
            "description": f"You're up {position.unrealized_pnl_pct:.0%} - consider locking in gains",
            "actions": [
                {"label": "Sell 50%", "template": f"Sell 50% of {symbol}"},
                {"label": "Set target at +50%", "template": f"Sell all {symbol} when it reaches ${position.avg_cost * 1.5:.0f}"},
                {"label": "Set trailing stop", "template": f"Set 10% trailing stop on {symbol}"},
            ],
        })

    if position.portfolio_weight > 0.25:
        suggestions.append({
            "id": "concentration_risk",
            "title": "⚠️ Concentration Risk",
            "description": f"{symbol} is {position.portfolio_weight:.0%} of your portfolio",
            "actions": [
                {"label": "Trim to 20%", "template": f"Reduce {symbol} to 20% of portfolio"},
                {"label": "Set rebalance rule", "template": f"If {symbol} exceeds 25% of portfolio, trim to 20%"},
            ],
        })

    if position.unrealized_pnl_pct < -0.10:
        suggestions.append({
            "id": "cut_losses",
            "title": "🚨 Cut Losses",
            "description": f"You're down {position.unrealized_pnl_pct:.0%}",
            "actions": [
                {"label": "Set stop at -15%", "template": f"Sell {symbol} if it drops 15% from here"},
                {"label": "Double down", "template": f"Buy more {symbol} if it drops 20% (average down)"},
            ],
        })

    # Generic suggestions
    suggestions.append({
        "id": "protect_gains",
        "title": "🛡️ Protect Your Position",
        "description": "Set a stop loss to limit downside",
        "actions": [
            {"label": "10% trailing stop", "template": f"Set 10% trailing stop on {symbol}"},
            {"label": "Fixed stop at -10%", "template": f"Sell {symbol} if it drops 10% from current price"},
        ],
    })

    return {"suggestions": suggestions}


@app.post("/api/strategies/parse", response_model=StrategyPreview)
async def parse_strategy(input: StrategyInput):
    """
    Parse natural language strategy and return interpretation.
    This is the first step - user sees preview before saving.
    """
    portfolio = state.get_portfolio()

    # Build context-aware prompt
    context = ""
    if input.symbol:
        position = next((p for p in portfolio.positions if p.symbol == input.symbol), None)
        if position:
            context = f"""
            The user owns {position.quantity} shares of {position.symbol}
            at an average cost of ${position.avg_cost:.2f}.
            Current price is ${position.current_price:.2f}.
            They are {'up' if position.unrealized_pnl > 0 else 'down'} {abs(position.unrealized_pnl_pct):.1%}.
            """

    # Parse using LLM
    prompt = f"""
    {context}

    The user wants to create a trading strategy: "{input.description}"

    Parse this into:
    1. A clear title (5 words max)
    2. Specific rules with exact prices/percentages
    3. Any ambiguous terms that need clarification
    4. Expected impact on their position

    Return JSON with:
    - title: string
    - interpretation: human-readable explanation
    - ambiguities: list of {term, options, default} objects
    - impact: {shares_involved, estimated_proceeds, concentration_change}
    - readable_rules: list of bullet points
    - confidence: 0-100 score
    """

    # Mock response for now - integrate with actual LLM
    preview = StrategyPreview(
        title="Profit Taking Strategy",
        interpretation=f"Sell 50% of {input.symbol} when it reaches $800",
        ambiguities=[
            {
                "term": "high price",
                "options": ["$800", "$850", "$900"],
                "default": "$800",
                "context": f"Current price is ${position.current_price if input.symbol else 0:.2f}",
            }
        ] if input.symbol else [],
        impact={
            "shares_to_sell": 40,
            "estimated_proceeds": 32000,
            "remaining_shares": 40,
            "concentration_before": "33%",
            "concentration_after": "16%",
        },
        confidence=85,
        readable_rules=[
            f"WHEN {input.symbol} reaches $800",
            f"SELL 40 shares (50% of position)",
            "SET trailing stop at 10% for remaining",
        ],
    )

    return preview


@app.post("/api/strategies")
async def create_strategy(request: StrategyCreateRequest):
    """
    Create a strategy after user confirmation.
    """
    # In real implementation, save to database
    strategy_id = f"strat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Create strategy object
    symbols = [request.symbol] if request.symbol else []

    strategy = PlainLanguageStrategy(
        id=strategy_id,
        name=f"Strategy for {request.symbol}",
        description=request.description,
        symbols=symbols,
        timeframe="1d",
        approval_mode=ApprovalMode(request.approval_mode),
    )

    state.strategies[strategy_id] = strategy
    state.strategy_repo.save(strategy)

    return {
        "id": strategy_id,
        "status": "created",
        "symbol": request.symbol,
        "message": f"Strategy created for {request.symbol}",
    }


@app.get("/api/strategies")
async def list_strategies():
    """List all active strategies."""
    return {
        "strategies": [
            {
                "id": s.id,
                "name": s.name,
                "symbols": s.symbols,
                "status": "active" if s.enabled else "paused",
                "approval_mode": s.approval_mode.value,
            }
            for s in state.strategies.values()
        ]
    }


@app.get("/api/alerts")
async def get_alerts() -> List[Alert]:
    """Get all active alerts."""
    return state.alerts


@app.get("/api/signals/pending")
async def get_pending_signals() -> List[Signal]:
    """Get signals awaiting approval."""
    return [s for s in state.signals if s.status == "pending"]


@app.post("/api/signals/{signal_id}/approve")
async def approve_signal(signal_id: str, action: str = "approve"):
    """Approve or reject a signal."""
    signal = next((s for s in state.signals if s.id == signal_id), None)
    if not signal:
        raise HTTPException(404, "Signal not found")

    signal.status = "approved" if action == "approve" else "rejected"

    # Broadcast update
    await state.broadcast_update({
        "type": "signal_updated",
        "signal_id": signal_id,
        "status": signal.status,
    })

    return {"status": signal.status}


@app.post("/api/chat")
async def chat(message: str):
    """
    Natural language chat interface for quick actions.
    Returns suggested actions the user can take.
    """
    # Add user message
    state.chat_history.append(ChatMessage(
        role="user",
        content=message,
        timestamp=datetime.now(),
    ))

    # Parse intent and generate response
    # This is where we'd use LLM to understand the request

    response_actions = []

    # Simple keyword matching for demo
    if "nvda" in message.lower() and "sell" in message.lower():
        response_actions = [
            {"type": "action", "label": "Sell 50% of NVDA", "endpoint": "/api/trade", "params": {"symbol": "NVDA", "percentage": 0.5}},
            {"type": "action", "label": "Set sell target at $800", "endpoint": "/api/strategies", "params": {"symbol": "NVDA", "target": 800}},
        ]
    elif "strategy" in message.lower():
        response_actions = [
            {"type": "navigate", "label": "View My Strategies", "path": "/strategies"},
            {"type": "action", "label": "Create New Strategy", "endpoint": "/api/strategies/parse"},
        ]

    response = ChatMessage(
        role="assistant",
        content=f"I understand: '{message}'. What would you like to do?",
        timestamp=datetime.now(),
        actions=response_actions,
    )

    state.chat_history.append(response)

    return {
        "response": response.content,
        "actions": response_actions,
    }


# ============================================================================
# WebSocket for Real-time Updates
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.connected_websockets.append(websocket)

    try:
        # Send initial portfolio state
        portfolio = state.get_portfolio()
        await websocket.send_json({
            "type": "portfolio_update",
            "data": portfolio.model_dump(),
        })

        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        state.connected_websockets.remove(websocket)


# ============================================================================
# Static Files (for serving built frontend)
# ============================================================================

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="web/dist"), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse("web/dist/index.html")
except:
    pass  # Development mode without built frontend


# ============================================================================
# Development Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.interfaces.web.main:app", host="0.0.0.0", port=8000)
