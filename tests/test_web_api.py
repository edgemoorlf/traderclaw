"""Tests for the TraderClaw web UI FastAPI backend."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

# Import app once at module level; state is a singleton we patch per-test.
from src.interfaces.web.main import app, state, Signal

CSV_PATH = "examples/positions_03-23-2026.csv"

# Symbols present in the real Fidelity CSV
REAL_SYMBOL = "BMNR"
HIGH_GAIN_SYMBOL = "BLSH"   # up ~100% in the CSV (unrealized_pnl_pct > 20%)


def _make_real_context():
    """Load context from the actual Fidelity CSV export."""
    from src.ai.orchestrator import PositionService
    ps = PositionService()
    return ps.load_from_csv(CSV_PATH)


def _make_ps(context):
    """Return a mock PositionService that returns the given context."""
    ps = MagicMock()
    ps.get_user_context = AsyncMock(return_value=context)
    return ps


@pytest.fixture
def client():
    """TestClient with real Fidelity CSV portfolio wired into the live state singleton."""
    original_ps = state.position_service
    state.position_service = _make_ps(_make_real_context())
    state.strategies = {}
    state.signals = []
    state.alerts = []
    try:
        yield TestClient(app)
    finally:
        state.position_service = original_ps
        state.strategies = {}
        state.signals = []
        state.alerts = []


@pytest.fixture
def client_empty():
    """TestClient whose portfolio raises ValueError (no CSV loaded)."""
    original_ps = state.position_service
    ps = MagicMock()
    ps.get_user_context = AsyncMock(side_effect=ValueError("No portfolio loaded"))
    state.position_service = ps
    state.strategies = {}
    state.signals = []
    state.alerts = []
    try:
        yield TestClient(app)
    finally:
        state.position_service = original_ps
        state.strategies = {}
        state.signals = []
        state.alerts = []


# ---------------------------------------------------------------------------
# GET /api/portfolio
# ---------------------------------------------------------------------------

class TestGetPortfolio:
    def test_returns_200(self, client):
        assert client.get("/api/portfolio").status_code == 200

    def test_schema(self, client):
        data = client.get("/api/portfolio").json()
        for field in ("total_value", "cash", "positions", "daily_change", "daily_change_pct"):
            assert field in data

    def test_positions_have_required_fields(self, client):
        positions = client.get("/api/portfolio").json()["positions"]
        assert len(positions) > 0
        for pos in positions:
            for field in ("symbol", "quantity", "avg_cost", "current_price",
                          "market_value", "unrealized_pnl", "unrealized_pnl_pct",
                          "portfolio_weight"):
                assert field in pos, f"Missing field: {field}"

    def test_empty_portfolio(self, client_empty):
        data = client_empty.get("/api/portfolio").json()
        assert data["positions"] == []
        assert data["total_value"] == 0.0


# ---------------------------------------------------------------------------
# POST /api/portfolio/import
# ---------------------------------------------------------------------------

class TestImportPortfolio:
    def test_import_success(self, client):
        state.position_service.load_from_csv = MagicMock(return_value=None)
        res = client.post("/api/portfolio/import", params={"file_path": "/tmp/fake.csv"})
        assert res.status_code == 200

    def test_import_failure_returns_400(self, client):
        state.position_service.load_from_csv = MagicMock(
            side_effect=FileNotFoundError("not found")
        )
        res = client.post("/api/portfolio/import", params={"file_path": "/nonexistent.csv"})
        assert res.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/portfolio/upload (real Fidelity CSV)
# ---------------------------------------------------------------------------

class TestUploadPortfolio:
    def test_upload_real_csv(self):
        """Upload the actual Fidelity CSV and verify positions are loaded."""
        # Use a fresh app state with a real PositionService
        from src.ai.orchestrator import PositionService
        original_ps = state.position_service
        state.position_service = PositionService()
        state.strategies = {}
        try:
            client = TestClient(app)
            with open(CSV_PATH, "rb") as f:
                res = client.post(
                    "/api/portfolio/upload",
                    files={"file": ("positions_03-23-2026.csv", f, "text/csv")},
                )
            assert res.status_code == 200, res.text
            data = res.json()
            assert len(data["positions"]) > 0
            symbols = [p["symbol"] for p in data["positions"]]
            assert REAL_SYMBOL in symbols
        finally:
            state.position_service = original_ps

    def test_upload_non_csv_returns_400(self, client):
        res = client.post(
            "/api/portfolio/upload",
            files={"file": ("data.txt", b"not a csv", "text/plain")},
        )
        assert res.status_code == 400

    def test_upload_replaces_previous_portfolio(self):
        """Uploading twice should reflect the latest data."""
        from src.ai.orchestrator import PositionService
        original_ps = state.position_service
        state.position_service = PositionService()
        state.strategies = {}
        try:
            client = TestClient(app)
            for _ in range(2):
                with open(CSV_PATH, "rb") as f:
                    res = client.post(
                        "/api/portfolio/upload",
                        files={"file": ("positions_03-23-2026.csv", f, "text/csv")},
                    )
                assert res.status_code == 200
            data = res.json()
            assert len(data["positions"]) > 0
        finally:
            state.position_service = original_ps


# ---------------------------------------------------------------------------
# GET /api/positions/{symbol}/suggestions
# ---------------------------------------------------------------------------

class TestPositionSuggestions:
    def test_known_symbol_returns_suggestions(self, client):
        res = client.get(f"/api/positions/{REAL_SYMBOL}/suggestions")
        assert res.status_code == 200
        data = res.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0

    def test_suggestion_has_required_fields(self, client):
        suggestions = client.get(f"/api/positions/{REAL_SYMBOL}/suggestions").json()["suggestions"]
        for s in suggestions:
            assert "id" in s
            assert "title" in s
            assert "actions" in s

    def test_unknown_symbol_returns_404(self, client):
        assert client.get("/api/positions/FAKE/suggestions").status_code == 404

    def test_high_gain_triggers_take_profits(self, client):
        from src.interfaces.web.main import Portfolio, Position
        high_gain_pos = Position(
            symbol="GAIN", quantity=10, avg_cost=100.0, current_price=130.0,
            market_value=1300.0, unrealized_pnl=300.0, unrealized_pnl_pct=0.30,
            portfolio_weight=0.10,
        )
        with patch.object(state, "get_portfolio", new=AsyncMock(return_value=Portfolio(
            total_value=13000.0, cash=0.0, positions=[high_gain_pos],
            daily_change=0.0, daily_change_pct=0.0,
        ))):
            suggestions = client.get("/api/positions/GAIN/suggestions").json()["suggestions"]
        # AI generates its own IDs — check that at least one suggestion mentions profit-taking
        all_text = " ".join(s["title"] + s["description"] for s in suggestions).lower()
        assert any(word in all_text for word in ["profit", "gain", "sell", "lock"])

    def test_always_includes_protect_gains(self, client):
        suggestions = client.get(f"/api/positions/{REAL_SYMBOL}/suggestions").json()["suggestions"]
        # Should always have at least one defensive/risk suggestion
        all_text = " ".join(s["title"] + s["description"] for s in suggestions).lower()
        assert any(word in all_text for word in ["stop", "loss", "protect", "risk", "cut", "down"])


# ---------------------------------------------------------------------------
# POST /api/strategies/parse
# ---------------------------------------------------------------------------

class TestParseStrategy:
    def test_returns_preview(self, client):
        res = client.post("/api/strategies/parse", json={
            "description": f"Sell half when {REAL_SYMBOL} hits $50",
            "symbol": REAL_SYMBOL,
        })
        assert res.status_code == 200
        data = res.json()
        for field in ("title", "interpretation", "ambiguities", "impact",
                      "confidence", "readable_rules"):
            assert field in data

    def test_without_symbol(self, client):
        res = client.post("/api/strategies/parse", json={
            "description": "Protect all my positions",
        })
        assert res.status_code == 200

    def test_missing_description_returns_422(self, client):
        assert client.post("/api/strategies/parse", json={"symbol": REAL_SYMBOL}).status_code == 422

    def test_confidence_is_numeric(self, client):
        data = client.post("/api/strategies/parse", json={
            "description": f"Sell {REAL_SYMBOL} at $50",
            "symbol": REAL_SYMBOL,
        }).json()
        assert isinstance(data["confidence"], (int, float))

    def test_readable_rules_is_list(self, client):
        data = client.post("/api/strategies/parse", json={
            "description": f"Sell {REAL_SYMBOL} at $50",
            "symbol": REAL_SYMBOL,
        }).json()
        assert isinstance(data["readable_rules"], list)


# ---------------------------------------------------------------------------
# POST /api/strategies
# ---------------------------------------------------------------------------

class TestCreateStrategy:
    def test_creates_strategy(self, client):
        res = client.post("/api/strategies", json={
            "description": f"Sell {REAL_SYMBOL} when it drops 10%",
            "symbol": REAL_SYMBOL,
            "approval_mode": "hybrid",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "created"
        assert "id" in data

    def test_strategy_id_is_unique(self, client):
        timestamps = ["20260327_100001", "20260327_100002", "20260327_100003"]
        with patch("src.interfaces.web.main.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.side_effect = timestamps
            ids = [
                client.post("/api/strategies", json={
                    "description": f"Sell {REAL_SYMBOL} at $30",
                    "symbol": REAL_SYMBOL,
                    "approval_mode": "hybrid",
                }).json()["id"]
                for _ in range(3)
            ]
        assert len(set(ids)) == 3

    def test_missing_description_returns_422(self, client):
        assert client.post("/api/strategies", json={"symbol": REAL_SYMBOL}).status_code == 422

    def test_invalid_approval_mode_returns_422(self, client):
        res = client.post("/api/strategies", json={
            "description": f"Sell {REAL_SYMBOL}",
            "symbol": REAL_SYMBOL,
            "approval_mode": "invalid_mode",
        })
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/strategies
# ---------------------------------------------------------------------------

class TestListStrategies:
    def test_returns_strategies_list(self, client):
        res = client.get("/api/strategies")
        assert res.status_code == 200
        assert "strategies" in res.json()

    def test_created_strategy_appears_in_list(self, client):
        client.post("/api/strategies", json={
            "description": f"Sell {REAL_SYMBOL} at $30",
            "symbol": REAL_SYMBOL,
            "approval_mode": "hybrid",
        })
        strategies = client.get("/api/strategies").json()["strategies"]
        assert any(REAL_SYMBOL in s["symbols"] for s in strategies)


# ---------------------------------------------------------------------------
# GET /api/alerts
# ---------------------------------------------------------------------------

class TestGetAlerts:
    def test_returns_list(self, client):
        res = client.get("/api/alerts")
        assert res.status_code == 200
        assert isinstance(res.json(), list)


# ---------------------------------------------------------------------------
# GET /api/signals/pending
# ---------------------------------------------------------------------------

class TestGetPendingSignals:
    def test_returns_list(self, client):
        res = client.get("/api/signals/pending")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_only_pending_signals_returned(self, client):
        state.signals = [
            Signal(
                id="s1", symbol=REAL_SYMBOL, action="SELL", quantity=10, price=21.0,
                reason="test", confidence=80, position_context={},
                portfolio_impact={}, status="pending", created_at=datetime.now(),
            ),
            Signal(
                id="s2", symbol=HIGH_GAIN_SYMBOL, action="BUY", quantity=5, price=39.0,
                reason="test", confidence=70, position_context={},
                portfolio_impact={}, status="approved", created_at=datetime.now(),
            ),
        ]
        pending = client.get("/api/signals/pending").json()
        assert all(s["status"] == "pending" for s in pending)


# ---------------------------------------------------------------------------
# POST /api/signals/{signal_id}/approve
# ---------------------------------------------------------------------------

class TestApproveSignal:
    def _inject(self, signal_id="sig1"):
        state.signals = [
            Signal(
                id=signal_id, symbol=REAL_SYMBOL, action="SELL", quantity=10,
                price=21.0, reason="test", confidence=80,
                position_context={}, portfolio_impact={},
                status="pending", created_at=datetime.now(),
            )
        ]

    def test_approve_signal(self, client):
        self._inject()
        res = client.post("/api/signals/sig1/approve", params={"action": "approve"})
        assert res.status_code == 200
        assert res.json()["status"] == "approved"

    def test_reject_signal(self, client):
        self._inject()
        res = client.post("/api/signals/sig1/approve", params={"action": "reject"})
        assert res.status_code == 200
        assert res.json()["status"] == "rejected"

    def test_unknown_signal_returns_404(self, client):
        state.signals = []
        assert client.post("/api/signals/nonexistent/approve").status_code == 404


# ---------------------------------------------------------------------------
# POST /api/chat
# ---------------------------------------------------------------------------

class TestChat:
    def _mock_orchestrator(self, recommendation="HOLD", symbol="BMNR", rationale="Test rationale"):
        from src.ai.strategy_agents import TradingDecision
        from src.ai.orchestrator import TradingAdvice, MarketDataPackage
        from datetime import datetime, timezone
        mock_orch = MagicMock()
        mock_orch.advise = AsyncMock(return_value=TradingAdvice(
            timestamp=datetime.now(timezone.utc),
            user_query="test",
            market_data=MarketDataPackage(
                timestamp=datetime.now(timezone.utc),
                market_summary="test",
                symbols={}, macro=None, polymarket_signals=[], data_sources=[],
            ),
            decision=TradingDecision(
                recommendation=recommendation, symbol=symbol, quantity=None,
                quantity_type="shares", confidence="medium", rationale=rationale,
                risks=[], timeframe="today",
            ),
            execution_mode="advisory",
            sources=[],
        ))
        return mock_orch

    def test_returns_response(self, client):
        with patch.object(state, "get_orchestrator", return_value=self._mock_orchestrator()):
            res = client.post("/api/chat", params={"message": "hello"})
        assert res.status_code == 200
        data = res.json()
        assert "response" in data
        assert "actions" in data

    def test_sell_recommendation_returns_action(self, client):
        with patch.object(state, "get_orchestrator", return_value=self._mock_orchestrator(recommendation="SELL", symbol=REAL_SYMBOL)):
            data = client.post("/api/chat", params={"message": f"should I sell {REAL_SYMBOL}?"}).json()
        assert len(data["actions"]) > 0
        assert any(REAL_SYMBOL in a["label"] for a in data["actions"])

    def test_hold_recommendation_returns_no_action(self, client):
        with patch.object(state, "get_orchestrator", return_value=self._mock_orchestrator(recommendation="HOLD")):
            data = client.post("/api/chat", params={"message": "what do you think?"}).json()
        assert data["actions"] == []

    def test_generic_message_returns_response(self, client):
        with patch.object(state, "get_orchestrator", return_value=self._mock_orchestrator(rationale="No clear signal")):
            res = client.post("/api/chat", params={"message": "what is the weather?"})
        assert res.status_code == 200
        assert isinstance(res.json()["response"], str)
