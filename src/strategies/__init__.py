"""Strategies module for TraderClaw.

This module provides:
- Plain language strategy definition and storage
- Strategy execution engine with multi-model consensus
- Hybrid approval flow (auto-execute vs ask user)
- Multi-account support for strategy comparison
"""

from .execution_engine import (
    StrategyExecutionEngine,
    PlainLanguageStrategy,
    StrategySignal,
    StrategyRepository,
    ConsensusEngine,
    ConsensusResult,
    ExecutionPlan,
    ApprovalMode,
    ConsensusType,
    get_execution_engine,
)

__all__ = [
    "StrategyExecutionEngine",
    "PlainLanguageStrategy",
    "StrategySignal",
    "StrategyRepository",
    "ConsensusEngine",
    "ConsensusResult",
    "ExecutionPlan",
    "ApprovalMode",
    "ConsensusType",
    "get_execution_engine",
]