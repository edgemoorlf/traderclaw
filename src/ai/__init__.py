"""AI module for TraderClaw.

This module provides the multi-model trading pipeline:
- GeminiDataAgent: Fetches fresh market data via Google Search
- StrategyAgents: Pluggable LLMs for trading strategy analysis
- TradingOrchestrator: Coordinates the entire pipeline
"""

from .gemini_data_agent import GeminiDataAgent, MarketDataPackage, SymbolData, MacroContext
from .strategy_agents import (
    StrategyAgent,
    StrategyModel,
    StrategyAgentFactory,
    TradingDecision,
    DeepSeekStrategyAgent,
    ClaudeStrategyAgent,
    QwenStrategyAgent,
)
from .orchestrator import TradingOrchestrator, TradingAdvice, PositionService

__all__ = [
    # Data Agent
    "GeminiDataAgent",
    "MarketDataPackage",
    "SymbolData",
    "MacroContext",
    # Strategy Agents
    "StrategyAgent",
    "StrategyModel",
    "StrategyAgentFactory",
    "TradingDecision",
    "DeepSeekStrategyAgent",
    "ClaudeStrategyAgent",
    "QwenStrategyAgent",
    # Orchestrator
    "TradingOrchestrator",
    "TradingAdvice",
    "PositionService",
]
