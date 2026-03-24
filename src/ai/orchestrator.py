"""Trading Orchestrator - Coordinates the multi-model trading pipeline.

This module provides the main entry point for trading decisions,
combining Gemini for data gathering and pluggable LLMs for strategy analysis.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any

from .gemini_data_agent import GeminiDataAgent, MarketDataPackage
from .strategy_agents import (
    StrategyAgent,
    StrategyModel,
    StrategyAgentFactory,
    TradingDecision,
)

logger = logging.getLogger(__name__)


@dataclass
class TradingAdvice:
    """Complete trading advice for the user."""
    timestamp: datetime
    user_query: str
    market_data: MarketDataPackage
    decision: TradingDecision
    execution_mode: str  # advisory, approval, autonomous
    sources: List[str]


class PositionService:
    """
    Service for fetching user's portfolio and position data.

    Supports:
    - CSV imports from brokers (Fidelity, Schwab, etc.)
    - Direct broker API sync (Alpaca, OKX)
    - Manual position entry
    """

    def __init__(self):
        self._csv_positions: Optional[Dict[str, Any]] = None
        self._csv_path: Optional[str] = None

    def load_from_csv(self, csv_path: str, broker: Optional[str] = None) -> Dict[str, Any]:
        """
        Load positions from broker CSV export.

        Args:
            csv_path: Path to CSV file from broker
            broker: Optional broker name for specific parser

        Returns:
            Portfolio context dictionary
        """
        from ..infrastructure.csv_importers import import_positions

        logger.info(f"Loading positions from CSV: {csv_path}")
        imported = import_positions(csv_path, broker)

        # Convert to internal format
        positions = {}
        total_value = Decimal("0")
        total_cost = Decimal("0")

        for pos in imported:
            if pos.quantity and pos.quantity > 0:
                positions[pos.symbol] = {
                    "quantity": float(pos.quantity),
                    "avg_entry_price": float(pos.avg_cost_basis) if pos.avg_cost_basis else None,
                    "current_price": float(pos.last_price) if pos.last_price else None,
                    "market_value": float(pos.current_value) if pos.current_value else None,
                    "unrealized_pnl_pct": float(pos.total_gain_loss_percent) if pos.total_gain_loss_percent else None,
                    "account": pos.account,
                    "account_type": pos.account_type,
                }

                if pos.current_value:
                    total_value += pos.current_value
                if pos.avg_cost_basis and pos.quantity:
                    total_cost += pos.avg_cost_basis * pos.quantity

        self._csv_positions = {
            "source": f"csv:{csv_path}",
            "total_portfolio_value": float(total_value),
            "total_cost_basis": float(total_cost),
            "unrealized_pnl_pct": float((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
            "positions": positions,
            "imported_at": datetime.utcnow().isoformat(),
        }
        self._csv_path = csv_path

        logger.info(f"Loaded {len(positions)} positions with total value ${total_value:,.2f}")
        return self._csv_positions

    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's portfolio context.

        Priority:
        1. CSV import if loaded
        2. Hardcoded demo data (for testing)

        Args:
            user_id: User identifier

        Returns:
            Dictionary with positions, strategy, preferences
        """
        # Return CSV positions if available
        if self._csv_positions:
            return {
                **self._csv_positions,
                "user_id": user_id,
                "risk_tolerance": "moderate",
                "strategy_description": "Growth with volatility harvesting",
                "target_profit_pct": 20,
                "stop_loss_pct": 10,
                "max_position_pct": 15,
            }

        # Fall back to demo data
        return self._get_demo_context(user_id)

    def _get_demo_context(self, user_id: str) -> Dict[str, Any]:
        """Demo portfolio for testing."""
        return {
            "user_id": user_id,
            "source": "demo",
            "total_portfolio_value": 150000.00,
            "cash_available": 45000.00,
            "risk_tolerance": "moderate",
            "strategy_description": "Growth with volatility harvesting",
            "target_profit_pct": 20,
            "stop_loss_pct": 10,
            "max_position_pct": 15,
            "positions": {
                "AAPL": {
                    "quantity": 100,
                    "avg_entry_price": 150.00,
                    "current_price": 185.50,
                    "market_value": 18550.00,
                    "unrealized_pnl_pct": 23.7,
                },
                "BTC": {
                    "quantity": 0.5,
                    "avg_entry_price": 40000.00,
                    "current_price": 67890.00,
                    "market_value": 33945.00,
                    "unrealized_pnl_pct": 69.7,
                }
            }
        }

    def get_position_symbols(self) -> List[str]:
        """Get list of position symbols."""
        if self._csv_positions:
            return list(self._csv_positions.get("positions", {}).keys())
        return []

    def get_positions_summary(self) -> str:
        """Get human-readable positions summary."""
        if not self._csv_positions:
            return "No positions loaded"

        positions = self._csv_positions.get("positions", {})
        lines = [f"Portfolio: ${self._csv_positions['total_portfolio_value']:,.2f}"]

        for symbol, pos in positions.items():
            pnl = pos.get('unrealized_pnl_pct')
            pnl_str = f"{pnl:+.1f}%" if pnl else "N/A"
            lines.append(f"  {symbol}: {pos['quantity']} shares @ ${pos.get('avg_entry_price', 'N/A')} (P&L: {pnl_str})")

        return "\n".join(lines)


class TradingOrchestrator:
    """
    Orchestrates the multi-model trading pipeline.

    Flow:
    1. Parse user query to identify relevant symbols
    2. Gemini fetches fresh market data via Google Search
    3. Fetch user's positions and strategy preferences
    4. Strategy model (DeepSeek/Claude/Qwen) analyzes and decides
    5. Return structured trading advice

    This design separates data gathering (Gemini + Search) from
    strategy analysis (pluggable LLMs) for optimal performance.
    """

    def __init__(
        self,
        gemini_api_key: str,
        strategy_model: StrategyModel = StrategyModel.DEEPSEEK,
        strategy_api_key: str = None,
        strategy_model_name: Optional[str] = None,
        execution_mode: str = "advisory",  # advisory, approval, autonomous
    ):
        """
        Initialize the trading orchestrator.

        Args:
            gemini_api_key: Google AI Studio API key for data gathering
            strategy_model: Which model to use for strategy analysis
            strategy_api_key: API key for the strategy model
            strategy_model_name: Specific model name (optional)
            execution_mode: How trades should be executed
        """
        self.data_agent = GeminiDataAgent(gemini_api_key)
        self.strategy_agent: StrategyAgent = StrategyAgentFactory.create(
            model=strategy_model,
            api_key=strategy_api_key,
            model_name=strategy_model_name,
        )
        self.position_service = PositionService()
        self.execution_mode = execution_mode

        logger.info(
            f"TradingOrchestrator initialized: "
            f"data=Gemini, strategy={strategy_model.value}, mode={execution_mode}"
        )

    async def advise(
        self,
        user_id: str,
        query: str,
        symbols: Optional[List[str]] = None
    ) -> TradingAdvice:
        """
        Main entry point for trading advice.

        This method coordinates the entire multi-model pipeline to provide
        actionable trading recommendations.

        Args:
            user_id: User identifier for fetching portfolio context
            query: Natural language question about trading
            symbols: Specific symbols to research (optional, extracted from query if not provided)

        Returns:
            TradingAdvice with complete analysis and recommendation
        """
        logger.info(f"Processing query for user {user_id}: {query}")
        start_time = datetime.utcnow()

        # Step 1: Identify symbols from query if not provided
        if not symbols:
            symbols = self._extract_symbols(query)
            logger.info(f"Extracted symbols: {symbols}")

        if not symbols:
            # Return error advice
            return self._create_error_advice(
                query, "No symbols found in query. Please specify tickers like AAPL, BTC, etc."
            )

        # Step 2: Fetch fresh market data via Gemini + Google Search
        logger.info(f"🔍 Gathering market data for: {symbols}")
        try:
            market_data = await self.data_agent.gather_market_data(symbols)
        except Exception as e:
            logger.error(f"Failed to gather market data: {e}")
            return self._create_error_advice(query, f"Data gathering failed: {e}")

        # Step 3: Also get Polymarket signals if relevant
        polymarket_topics = self._extract_polymarket_topics(query, symbols)
        if polymarket_topics:
            logger.info(f"🔮 Searching Polymarket for: {polymarket_topics}")
            try:
                polymarket_signals = await self.data_agent.search_polymarket_signals(
                    polymarket_topics
                )
                market_data.polymarket_signals = polymarket_signals
            except Exception as e:
                logger.warning(f"Failed to fetch Polymarket data: {e}")

        # Step 4: Get macro context for broader picture
        logger.info("📊 Fetching macro context...")
        try:
            macro_data = await self.data_agent.get_macro_context()
            market_data.macro = macro_data
        except Exception as e:
            logger.warning(f"Failed to fetch macro context: {e}")

        # Step 5: Fetch user's portfolio context
        logger.info(f"📈 Fetching portfolio context for user {user_id}...")
        try:
            user_context = await self.position_service.get_user_context(user_id)
        except Exception as e:
            logger.error(f"Failed to fetch user context: {e}")
            return self._create_error_advice(query, f"Portfolio fetch failed: {e}")

        # Step 6: Strategy model analyzes and makes decision
        logger.info(f"🧠 Analyzing with {self.strategy_agent.name}...")
        try:
            decision = await self.strategy_agent.analyze(
                market_data=self._package_for_strategy(market_data),
                user_context=user_context,
                query=query,
            )
        except Exception as e:
            logger.error(f"Strategy analysis failed: {e}")
            return self._create_error_advice(query, f"Analysis failed: {e}")

        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Advice generated in {processing_time:.2f}s: {decision.recommendation}")

        # Step 7: Return complete advice package
        return TradingAdvice(
            timestamp=datetime.utcnow(),
            user_query=query,
            market_data=market_data,
            decision=decision,
            execution_mode=self.execution_mode,
            sources=["google_search", "polymarket", "portfolio_db"],
        )

    def _extract_symbols(self, query: str) -> List[str]:
        """
        Extract stock/crypto symbols from natural language query.

        Args:
            query: User's question

        Returns:
            List of ticker symbols
        """
        # Common words to exclude (not tickers)
        common_words = {
            'A', 'I', 'US', 'USD', 'ETF', 'IPO', 'CEO', 'CFO', 'EPS', 'GDP',
            'FED', 'IRS', 'SEC', 'NYSE', 'NASDAQ', 'THE', 'AND', 'FOR',
            'BUY', 'SELL', 'HOLD', 'MY', 'ME', 'IT', 'IS', 'AT', 'BE',
        }

        # Match 1-5 uppercase letters (standard ticker format)
        import re
        tickers = re.findall(r'\b[A-Z]{1,5}\b', query.upper())

        # Filter out common words
        tickers = [t for t in tickers if t not in common_words]

        # Remove duplicates while preserving order
        seen = set()
        unique_tickers = []
        for t in tickers:
            if t not in seen:
                seen.add(t)
                unique_tickers.append(t)

        return unique_tickers

    def _extract_polymarket_topics(
        self,
        query: str,
        symbols: List[str]
    ) -> List[str]:
        """
        Extract topics relevant for Polymarket search.

        Args:
            query: User's question
            symbols: Extracted symbols

        Returns:
            List of topics to search on Polymarket
        """
        topics = []

        # Add symbols as topics
        topics.extend(symbols)

        # Extract event-related keywords
        query_lower = query.lower()

        # Common event keywords
        event_keywords = [
            "election", "fed", "rate", "inflation", "recession",
            "earnings", "approval", "etf", "regulation", "war",
            "bitcoin", "crypto", "president", "vote", "cpi"
        ]

        for keyword in event_keywords:
            if keyword in query_lower:
                topics.append(keyword)

        # Remove duplicates
        return list(set(topics))

    def _package_for_strategy(self, market_data: MarketDataPackage) -> Dict[str, Any]:
        """
        Convert MarketDataPackage to dict for strategy agent.

        Args:
            market_data: Data from GeminiDataAgent

        Returns:
            Dictionary suitable for strategy agent
        """
        return {
            "timestamp": market_data.timestamp.isoformat(),
            "market_summary": market_data.market_summary,
            "symbols": {
                symbol: {
                    "price": data.price,
                    "change_24h": data.change_24h,
                    "change_1h": data.change_1h,
                    "key_news": data.key_news,
                    "upcoming_events": data.upcoming_events,
                    "sentiment": data.sentiment,
                }
                for symbol, data in market_data.symbols.items()
            },
            "polymarket_signals": market_data.polymarket_signals,
            "macro": {
                "vix": market_data.macro.vix if market_data.macro else None,
                "fed_policy": market_data.macro.fed_policy if market_data.macro else "unknown",
                "market_regime": market_data.macro.market_regime if market_data.macro else "unknown",
                "major_events": market_data.macro.major_events if market_data.macro else [],
            } if market_data.macro else None,
        }

    def _create_error_advice(self, query: str, error: str) -> TradingAdvice:
        """Create error TradingAdvice."""
        from .gemini_data_agent import MarketDataPackage, SymbolData

        return TradingAdvice(
            timestamp=datetime.utcnow(),
            user_query=query,
            market_data=MarketDataPackage(
                timestamp=datetime.utcnow(),
                market_summary=f"Error: {error}",
                symbols={},
                macro=None,
                polymarket_signals=[],
                data_sources=[],
            ),
            decision=TradingDecision(
                recommendation="HOLD",
                symbol="UNKNOWN",
                quantity=None,
                quantity_type="shares",
                confidence="low",
                rationale=f"Error processing request: {error}",
                risks=["System error - manual review required"],
                timeframe="immediate",
            ),
            execution_mode=self.execution_mode,
            sources=[],
        )

    async def morning_briefing(self, user_id: str) -> TradingAdvice:
        """
        Generate a morning briefing for the user.

        Args:
            user_id: User identifier

        Returns:
            TradingAdvice with portfolio overview and recommendations
        """
        # Get user's positions
        user_context = await self.position_service.get_user_context(user_id)
        positions = list(user_context.get("positions", {}).keys())

        if not positions:
            return await self.advise(
                user_id=user_id,
                query="What's the market outlook today? Any opportunities?"
            )

        # Create comprehensive briefing query
        query = f"""Good morning! Review my portfolio: {', '.join(positions)}.
What's changed overnight? Any actions needed?"""

        return await self.advise(user_id=user_id, query=query, symbols=positions)

    def get_config(self) -> Dict[str, str]:
        """Get current orchestrator configuration."""
        return {
            "data_agent": "Gemini (Google Search)",
            "strategy_agent": self.strategy_agent.name,
            "execution_mode": self.execution_mode,
            "available_strategy_models": StrategyAgentFactory.list_available(),
        }
