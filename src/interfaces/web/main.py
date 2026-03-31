"""Web UI backend for TraderClaw.

Provides REST API and WebSocket endpoints for the single-screen dashboard.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
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
    allow_origins=["*"],
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
# Global State
# ============================================================================

class AppState:
    def __init__(self):
        self.position_service = PositionService()
        self.strategy_repo = StrategyRepository()
        self.broker_manager = get_broker_manager()
        # Seed in-memory cache from DB so strategies survive restarts
        self.strategies: Dict[str, PlainLanguageStrategy] = {
            s.id: s for s in self.strategy_repo.load_all()
        }
        self.signals: List[Signal] = []
        self.alerts: List[Alert] = []
        self.chat_history: List[ChatMessage] = []
        self.connected_websockets: List[WebSocket] = []
        self._orchestrator = None

    def get_orchestrator(self):
        if self._orchestrator is None:
            import os
            from dotenv import load_dotenv
            load_dotenv("config/.env")
            from src.ai.orchestrator import TradingOrchestrator
            from src.ai.strategy_agents import StrategyModel
            provider = os.getenv("STRATEGY_MODEL_PROVIDER", "deepseek").lower()
            model_map = {
                "deepseek": (StrategyModel.DEEPSEEK, os.getenv("DEEPSEEK_API_KEY")),
                "claude": (StrategyModel.CLAUDE, os.getenv("ANTHROPIC_API_KEY")),
                "qwen": (StrategyModel.QWEN, os.getenv("DASHSCOPE_API_KEY")),
                "gpt": (StrategyModel.GPT, os.getenv("OPENAI_API_KEY")),
            }
            model, api_key = model_map.get(provider, model_map["deepseek"])
            self._orchestrator = TradingOrchestrator(
                gemini_api_key=os.getenv("GEMINI_API_KEY"),
                strategy_model=model,
                strategy_api_key=api_key,
            )
            # Share the same position_service so CSV data is available
            self._orchestrator.position_service = self.position_service
        return self._orchestrator

    async def get_portfolio(self) -> Portfolio:
        """Get current portfolio state."""
        try:
            user_context = await self.position_service.get_user_context("default")
        except ValueError:
            user_context = None

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
    return await state.get_portfolio()


@app.post("/api/portfolio/import", response_model=Portfolio)
async def import_portfolio(file_path: str):
    """Import portfolio from CSV file path (server-side path)."""
    try:
        state.position_service.load_from_csv(file_path)
        return await state.get_portfolio()
    except Exception as e:
        raise HTTPException(400, f"Failed to import: {str(e)}")


@app.post("/api/portfolio/upload", response_model=Portfolio)
async def upload_portfolio(file: UploadFile = File(...)):
    """Upload and import a Fidelity CSV file from the browser."""
    import tempfile, os
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(400, "Please upload a .csv file")
    try:
        contents = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        state.position_service.load_from_csv(tmp_path)
        os.unlink(tmp_path)
        return await state.get_portfolio()
    except Exception as e:
        raise HTTPException(400, f"Failed to import: {str(e)}")


@app.get("/api/positions/{symbol}/suggestions")
async def get_position_suggestions(symbol: str):
    """Get AI-generated strategy suggestions for a specific position."""
    portfolio = await state.get_portfolio()
    position = next((p for p in portfolio.positions if p.symbol == symbol), None)

    if not position:
        raise HTTPException(404, f"Position not found: {symbol}")

    prompt = f"""You are a trading advisor. The user holds this position:

Symbol: {symbol}
Shares: {position.quantity}
Avg cost: ${position.avg_cost:.2f}
Current price: ${position.current_price:.2f}
Unrealized P&L: {position.unrealized_pnl_pct:+.1%} (${position.unrealized_pnl:.2f})
Portfolio weight: {position.portfolio_weight:.1%}

Suggest 3-4 concrete, actionable trading strategies for this position.
Each suggestion should be something the user can immediately act on.

Return JSON array:
[
  {{
    "id": "short_snake_case_id",
    "title": "Short title (emoji + 3-5 words)",
    "description": "One sentence explaining why",
    "actions": [
      {{"label": "Button label", "template": "Natural language rule the user can save, e.g. Sell 50% of {symbol} when it reaches $X"}}
    ]
  }}
]

Return only valid JSON, no markdown."""

    try:
        orchestrator = state.get_orchestrator()
        raw = await orchestrator.strategy_agent._call_llm(prompt)
        import json as _json
        data = _json.loads(orchestrator.strategy_agent._extract_json(raw))
        return {"suggestions": data}
    except Exception as e:
        # Fallback to rule-based suggestions
        suggestions = []
        if position.unrealized_pnl_pct > 0.20:
            suggestions.append({
                "id": "take_profits",
                "title": "🎯 Take Some Profits",
                "description": f"You're up {position.unrealized_pnl_pct:.0%} — consider locking in gains",
                "actions": [
                    {"label": "Sell 50%", "template": f"Sell 50% of {symbol}"},
                    {"label": "Set trailing stop", "template": f"Set 10% trailing stop on {symbol}"},
                ],
            })
        if position.unrealized_pnl_pct < -0.10:
            suggestions.append({
                "id": "cut_losses",
                "title": "🚨 Manage Downside",
                "description": f"You're down {position.unrealized_pnl_pct:.0%}",
                "actions": [
                    {"label": "Set stop at -15%", "template": f"Sell {symbol} if it drops 15% from here"},
                    {"label": "Average down", "template": f"Buy more {symbol} if it drops another 10%"},
                ],
            })
        suggestions.append({
            "id": "protect_gains",
            "title": "🛡️ Protect Position",
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
    portfolio = await state.get_portfolio()

    position = None
    if input.symbol:
        position = next((p for p in portfolio.positions if p.symbol == input.symbol), None)

    context = ""
    if position:
        context = (
            f"The user owns {position.quantity} shares of {position.symbol} "
            f"at an average cost of ${position.avg_cost:.2f}. "
            f"Current price is ${position.current_price:.2f}. "
            f"They are {'up' if position.unrealized_pnl > 0 else 'down'} {abs(position.unrealized_pnl_pct):.1%}."
        )

    prompt = f"""{context}

The user wants to create a trading strategy: "{input.description}"

Parse this into a JSON object with these exact fields:
- title: string (5 words max)
- interpretation: string (human-readable explanation of what will happen)
- ambiguities: list of objects with {{term, options, default}} for any unclear terms
- impact: object with {{shares_involved, estimated_proceeds, concentration_change}}
- readable_rules: list of bullet point strings
- confidence: integer 0-100

Return only valid JSON, no markdown."""

    try:
        orchestrator = state.get_orchestrator()
        agent = orchestrator.strategy_agent
        raw_text = await agent._call_llm(prompt)
        import json as _json
        data = _json.loads(agent._extract_json(raw_text))
        preview = StrategyPreview(
            title=data.get("title", "Custom Strategy"),
            interpretation=data.get("interpretation", input.description),
            ambiguities=data.get("ambiguities", []),
            impact=data.get("impact", {}),
            confidence=data.get("confidence", 70),
            readable_rules=data.get("readable_rules", [input.description]),
        )
    except Exception as e:
        preview = StrategyPreview(
            title="Custom Strategy",
            interpretation=input.description,
            ambiguities=[],
            impact={},
            confidence=50,
            readable_rules=[input.description],
        )

    return preview


@app.post("/api/strategies")
async def create_strategy(request: StrategyCreateRequest):
    """
    Create a strategy after user confirmation.
    """
    strategy_id = f"strat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Create strategy object
    symbols = [request.symbol] if request.symbol else []

    try:
        approval_mode = ApprovalMode(request.approval_mode)
    except ValueError:
        raise HTTPException(422, f"Invalid approval_mode: {request.approval_mode!r}")

    strategy = PlainLanguageStrategy(
        id=strategy_id,
        name=f"Strategy for {request.symbol}",
        description=request.description,
        symbols=symbols,
        timeframe="1d",
        approval_mode=approval_mode,
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

    try:
        orchestrator = state.get_orchestrator()
        advice = await orchestrator.advise(user_id="default", query=message)
        response_text = advice.decision.rationale
        response_actions = []
        rec = advice.decision.recommendation.upper()
        symbol = advice.decision.symbol
        if rec in ("BUY", "SELL") and symbol and symbol != "UNKNOWN":
            response_actions.append({
                "type": "action",
                "label": f"{rec} {symbol}",
                "endpoint": "/api/trade",
                "params": {"symbol": symbol, "action": rec},
            })
    except ValueError as e:
        # No CSV loaded
        response_text = str(e)
        response_actions = []
    except Exception as e:
        response_text = f"Analysis failed: {e}"
        response_actions = []

    response = ChatMessage(
        role="assistant",
        content=response_text,
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
        portfolio = await state.get_portfolio()
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
