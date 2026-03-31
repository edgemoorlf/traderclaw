"""SQLite persistence layer for TraderClaw runtime data."""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "data/traderclaw.db"


def _ensure_dir(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def _connect(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Create tables if they don't exist."""
    _ensure_dir(db_path)
    with _connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                symbols TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                position_sizing TEXT NOT NULL,
                max_positions INTEGER NOT NULL,
                stop_loss_rule TEXT,
                take_profit_rule TEXT,
                approval_mode TEXT NOT NULL,
                auto_execute_confidence_threshold REAL NOT NULL,
                use_consensus INTEGER NOT NULL,
                consensus_type TEXT NOT NULL,
                consensus_models TEXT NOT NULL,
                model_weights TEXT NOT NULL,
                indicators TEXT NOT NULL,
                enabled INTEGER NOT NULL,
                tags TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
    logger.info(f"Database initialised at {db_path}")


class StrategyRepository:
    """SQLite-backed repository for plain language strategies."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        init_db(db_path)

    def save(self, strategy) -> None:
        with _connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO strategies VALUES (
                    :id, :name, :description, :symbols, :timeframe,
                    :position_sizing, :max_positions, :stop_loss_rule,
                    :take_profit_rule, :approval_mode,
                    :auto_execute_confidence_threshold, :use_consensus,
                    :consensus_type, :consensus_models, :model_weights,
                    :indicators, :enabled, :tags, :created_at, :updated_at
                )
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    description=excluded.description,
                    symbols=excluded.symbols,
                    timeframe=excluded.timeframe,
                    position_sizing=excluded.position_sizing,
                    max_positions=excluded.max_positions,
                    stop_loss_rule=excluded.stop_loss_rule,
                    take_profit_rule=excluded.take_profit_rule,
                    approval_mode=excluded.approval_mode,
                    auto_execute_confidence_threshold=excluded.auto_execute_confidence_threshold,
                    use_consensus=excluded.use_consensus,
                    consensus_type=excluded.consensus_type,
                    consensus_models=excluded.consensus_models,
                    model_weights=excluded.model_weights,
                    indicators=excluded.indicators,
                    enabled=excluded.enabled,
                    tags=excluded.tags,
                    updated_at=excluded.updated_at
            """, self._to_row(strategy))
        logger.info(f"Saved strategy: {strategy.id}")

    def load(self, strategy_id: str) -> Optional[Any]:
        with _connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM strategies WHERE id = ?", (strategy_id,)
            ).fetchone()
        return self._from_row(dict(row)) if row else None

    def load_all(self) -> List[Any]:
        with _connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM strategies ORDER BY created_at"
            ).fetchall()
        return [self._from_row(dict(r)) for r in rows]

    def delete(self, strategy_id: str) -> bool:
        with _connect(self.db_path) as conn:
            cur = conn.execute(
                "DELETE FROM strategies WHERE id = ?", (strategy_id,)
            )
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_row(self, s) -> dict:
        return {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "symbols": json.dumps(s.symbols),
            "timeframe": s.timeframe,
            "position_sizing": s.position_sizing,
            "max_positions": s.max_positions,
            "stop_loss_rule": s.stop_loss_rule,
            "take_profit_rule": s.take_profit_rule,
            "approval_mode": s.approval_mode.value,
            "auto_execute_confidence_threshold": s.auto_execute_confidence_threshold,
            "use_consensus": int(s.use_consensus),
            "consensus_type": s.consensus_type.value,
            "consensus_models": json.dumps([m.value for m in s.consensus_models]),
            "model_weights": json.dumps(s.model_weights),
            "indicators": json.dumps(s.indicators),
            "enabled": int(s.enabled),
            "tags": json.dumps(s.tags),
            "created_at": s.created_at.isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def _from_row(self, row: dict) -> Any:
        # Import here to avoid circular imports
        from src.strategies.execution_engine import (
            PlainLanguageStrategy, ApprovalMode, ConsensusType,
        )
        from src.ai.strategy_agents import StrategyModel

        return PlainLanguageStrategy(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            symbols=json.loads(row["symbols"]),
            timeframe=row["timeframe"],
            position_sizing=row["position_sizing"],
            max_positions=row["max_positions"],
            stop_loss_rule=row["stop_loss_rule"],
            take_profit_rule=row["take_profit_rule"],
            approval_mode=ApprovalMode(row["approval_mode"]),
            auto_execute_confidence_threshold=row["auto_execute_confidence_threshold"],
            use_consensus=bool(row["use_consensus"]),
            consensus_type=ConsensusType(row["consensus_type"]),
            consensus_models=[StrategyModel(m) for m in json.loads(row["consensus_models"])],
            model_weights=json.loads(row["model_weights"]),
            indicators=json.loads(row["indicators"]),
            enabled=bool(row["enabled"]),
            tags=json.loads(row["tags"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
