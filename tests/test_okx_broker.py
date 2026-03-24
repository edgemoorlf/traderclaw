"""Unit tests for OKX broker."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import responses

from src.infrastructure.brokers.okx_broker import OKXBroker
from src.application.interfaces.broker import (
    Order, OrderSide, OrderType, OrderStatus
)


class TestOKXBroker:
    """Test OKX broker implementation."""

    @pytest.fixture
    def broker(self):
        return OKXBroker(
            api_key="test_key",
            api_secret="test_secret",
            passphrase="test_passphrase",
            paper=True
        )

    @responses.activate
    @pytest.mark.asyncio
    async def test_connect_success(self, broker):
        """Test successful connection."""
        responses.add(
            responses.GET,
            "https://www.okx.com/api/v5/account/balance",
            json={
                "code": "0",
                "data": [{
                    "details": [
                        {"ccy": "USDT", "eq": "10000", "cashBal": "10000", "availBal": "9000"},
                        {"ccy": "BTC", "eq": "0.5", "cashBal": "0.5"},
                    ]
                }]
            },
            status=200
        )

        result = await broker.connect()

        assert result is True
        assert broker.is_connected() is True
        assert broker.is_paper() is True

    @responses.activate
    @pytest.mark.asyncio
    async def test_connect_failure(self, broker):
        """Test connection failure."""
        responses.add(
            responses.GET,
            "https://www.okx.com/api/v5/account/balance",
            json={"code": "1", "msg": "Invalid API key"},
            status=200
        )

        result = await broker.connect()
        assert result is False

    @pytest.mark.asyncio
    async def test_connect_missing_credentials(self):
        """Test connection without credentials."""
        broker = OKXBroker(api_key=None, api_secret=None, passphrase=None)
        result = await broker.connect()
        assert result is False

    @responses.activate
    @pytest.mark.asyncio
    async def test_get_account_balance(self, broker):
        """Test fetching account balance."""
        responses.add(
            responses.GET,
            "https://www.okx.com/api/v5/account/balance",
            json={
                "code": "0",
                "data": [{
                    "details": [
                        {"ccy": "USDT", "eq": "10000", "cashBal": "10000", "availBal": "9000"},
                        {"ccy": "BTC", "eq": "0.5", "cashBal": "0.5"},
                    ]
                }]
            },
            status=200
        )

        await broker.connect()
        balance = await broker.get_account_balance()

        assert balance.currency == "USDT"
        assert balance.cash == Decimal("10000")
        assert balance.buying_power == Decimal("9000")
        assert balance.equity == Decimal("10000.5")  # 10000 USDT + 0.5 BTC

    @responses.activate
    @pytest.mark.asyncio
    async def test_place_market_order(self, broker):
        """Test placing a market order."""
        # First connect
        responses.add(
            responses.GET,
            "https://www.okx.com/api/v5/account/balance",
            json={"code": "0", "data": [{"details": []}]},
            status=200
        )

        # Then place order
        responses.add(
            responses.POST,
            "https://www.okx.com/api/v5/trade/order",
            json={
                "code": "0",
                "data": [{
                    "ordId": "123456",
                    "instId": "BTC-USDT",
                    "side": "buy",
                    "ordType": "market",
                    "sz": "0.01",
                    "accFillSz": "0.01",
                    "avgPx": "50000",
                    "state": "filled",
                    "cTime": "2024-01-01T00:00:00.000Z",
                    "uTime": "2024-01-01T00:00:01.000Z",
                }]
            },
            status=200
        )

        await broker.connect()

        order = Order(
            symbol="BTC-USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.01"),
        )

        result = await broker.place_order(order)

        assert result.order_id == "123456"
        assert result.symbol == "BTC-USDT"
        assert result.side == OrderSide.BUY
        assert result.status == OrderStatus.FILLED
        assert result.filled_quantity == Decimal("0.01")
        assert result.avg_fill_price == Decimal("50000")

    @responses.activate
    @pytest.mark.asyncio
    async def test_place_limit_order(self, broker):
        """Test placing a limit order."""
        # Connect
        responses.add(
            responses.GET,
            "https://www.okx.com/api/v5/account/balance",
            json={"code": "0", "data": [{"details": []}]},
            status=200
        )

        # Place order
        responses.add(
            responses.POST,
            "https://www.okx.com/api/v5/trade/order",
            json={
                "code": "0",
                "data": [{
                    "ordId": "789012",
                    "instId": "ETH-USDT",
                    "side": "sell",
                    "ordType": "limit",
                    "sz": "1.0",
                    "accFillSz": "0",
                    "avgPx": "",
                    "state": "live",
                    "cTime": "2024-01-01T00:00:00.000Z",
                }]
            },
            status=200
        )

        await broker.connect()

        order = Order(
            symbol="ETH-USDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("3000.00"),
        )

        result = await broker.place_order(order)

        assert result.order_id == "789012"
        assert result.status == OrderStatus.OPEN
        assert result.filled_quantity == Decimal("0")

    @responses.activate
    @pytest.mark.asyncio
    async def test_get_positions(self, broker):
        """Test fetching positions."""
        # Connect
        responses.add(
            responses.GET,
            "https://www.okx.com/api/v5/account/balance",
            json={"code": "0", "data": [{"details": []}]},
            status=200
        )

        # Get positions uses same endpoint
        responses.add(
            responses.GET,
            "https://www.okx.com/api/v5/account/balance",
            json={
                "code": "0",
                "data": [{
                    "details": [
                        {"ccy": "USDT", "eq": "5000", "cashBal": "5000", "avgPx": "1"},
                        {"ccy": "BTC", "eq": "0.1", "cashBal": "0.1", "avgPx": "45000"},
                    ]
                }]
            },
            status=200
        )

        await broker.connect()
        positions = await broker.get_positions()

        assert len(positions) == 2
        assert positions[0].symbol == "USDT"
        assert positions[1].symbol == "BTC"
        assert positions[1].quantity == Decimal("0.1")
        assert positions[1].avg_entry_price == Decimal("45000")

    @responses.activate
    @pytest.mark.asyncio
    async def test_cancel_order(self, broker):
        """Test canceling an order."""
        # Connect
        responses.add(
            responses.GET,
            "https://www.okx.com/api/v5/account/balance",
            json={"code": "0", "data": [{"details": []}]},
            status=200
        )

        # Cancel order
        responses.add(
            responses.POST,
            "https://www.okx.com/api/v5/trade/cancel-order",
            json={"code": "0", "data": [{"ordId": "123456"}]},
            status=200
        )

        await broker.connect()
        result = await broker.cancel_order("123456", symbol="BTC-USDT")

        assert result is True

    @responses.activate
    @pytest.mark.asyncio
    async def test_get_open_orders(self, broker):
        """Test fetching open orders."""
        # Connect
        responses.add(
            responses.GET,
            "https://www.okx.com/api/v5/account/balance",
            json={"code": "0", "data": [{"details": []}]},
            status=200
        )

        # Get orders
        responses.add(
            responses.GET,
            "https://www.okx.com/api/v5/trade/orders-pending",
            json={
                "code": "0",
                "data": [
                    {
                        "ordId": "111",
                        "instId": "BTC-USDT",
                        "side": "buy",
                        "ordType": "limit",
                        "sz": "0.01",
                        "accFillSz": "0",
                        "avgPx": "",
                        "state": "live",
                        "cTime": "2024-01-01T00:00:00.000Z",
                    }
                ]
            },
            status=200
        )

        await broker.connect()
        orders = await broker.get_open_orders()

        assert len(orders) == 1
        assert orders[0].order_id == "111"
        assert orders[0].status == OrderStatus.OPEN

    def test_generate_signature(self, broker):
        """Test HMAC-SHA256 signature generation."""
        timestamp = "2024-01-01T00:00:00.000Z"
        method = "GET"
        path = "/api/v5/account/balance"
        body = ""

        signature = broker._generate_signature(timestamp, method, path, body)

        # Signature should be base64 encoded
        assert isinstance(signature, str)
        assert len(signature) > 0
