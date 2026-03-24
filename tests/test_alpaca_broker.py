"""Unit tests for Alpaca broker."""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from src.infrastructure.brokers.alpaca_broker import AlpacaBroker
from src.application.interfaces.broker import (
    Order, OrderSide, OrderType, OrderStatus
)


class TestAlpacaBroker:
    """Test Alpaca broker implementation."""

    @pytest.fixture
    def broker(self):
        return AlpacaBroker(
            api_key="test_key",
            api_secret="test_secret",
            paper=True
        )

    @pytest.fixture
    def mock_alpaca_account(self):
        """Mock Alpaca account object."""
        account = Mock()
        account.account_number = "PA12345678"
        account.cash = "10000.00"
        account.buying_power = "20000.00"
        account.equity = "15000.00"
        account.initial_margin = "0.00"
        return account

    @pytest.mark.asyncio
    async def test_connect_success(self, broker, mock_alpaca_account):
        """Test successful connection to paper trading."""
        with patch('src.infrastructure.brokers.alpaca_broker.TradingClient') as mock_client:
            mock_instance = Mock()
            mock_instance.get_account.return_value = mock_alpaca_account
            mock_client.return_value = mock_instance

            result = await broker.connect()

            assert result is True
            assert broker.is_connected() is True
            assert broker.is_paper() is True
            mock_client.assert_called_once_with(
                api_key="test_key",
                secret_key="test_secret",
                paper=True
            )

    @pytest.mark.asyncio
    async def test_connect_missing_credentials(self):
        """Test connection without credentials."""
        broker = AlpacaBroker(api_key=None, api_secret=None)
        result = await broker.connect()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_account_balance(self, broker, mock_alpaca_account):
        """Test fetching account balance."""
        with patch('src.infrastructure.brokers.alpaca_broker.TradingClient') as mock_client:
            mock_instance = Mock()
            mock_instance.get_account.return_value = mock_alpaca_account
            mock_client.return_value = mock_instance

            await broker.connect()
            balance = await broker.get_account_balance()

            assert balance.currency == "USD"
            assert balance.cash == Decimal("10000.00")
            assert balance.buying_power == Decimal("20000.00")
            assert balance.equity == Decimal("15000.00")

    @pytest.mark.asyncio
    async def test_place_market_order(self, broker):
        """Test placing a market order."""
        mock_order = Mock()
        mock_order.id = "order-123"
        mock_order.symbol = "AAPL"
        mock_order.side.value = "buy"
        mock_order.type.value = "market"
        mock_order.qty = "10"
        mock_order.filled_qty = "10"
        mock_order.filled_avg_price = "150.00"
        mock_order.created_at = datetime.now()
        mock_order.updated_at = datetime.now()
        mock_order.status.value = "filled"

        with patch('src.infrastructure.brokers.alpaca_broker.TradingClient') as mock_client:
            mock_instance = Mock()
            mock_instance.submit_order.return_value = mock_order
            mock_client.return_value = mock_instance

            await broker.connect()

            order = Order(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal("10"),
            )

            result = await broker.place_order(order)

            assert result.order_id == "order-123"
            assert result.symbol == "AAPL"
            assert result.side == OrderSide.BUY
            assert result.status == OrderStatus.FILLED
            assert result.filled_quantity == Decimal("10")

    @pytest.mark.asyncio
    async def test_place_limit_order(self, broker):
        """Test placing a limit order."""
        mock_order = Mock()
        mock_order.id = "order-456"
        mock_order.symbol = "TSLA"
        mock_order.side.value = "sell"
        mock_order.type.value = "limit"
        mock_order.qty = "5"
        mock_order.filled_qty = "0"
        mock_order.filled_avg_price = None
        mock_order.created_at = datetime.now()
        mock_order.updated_at = None
        mock_order.status.value = "new"

        with patch('src.infrastructure.brokers.alpaca_broker.TradingClient') as mock_client:
            mock_instance = Mock()
            mock_instance.submit_order.return_value = mock_order
            mock_client.return_value = mock_instance

            await broker.connect()

            order = Order(
                symbol="TSLA",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=Decimal("5"),
                price=Decimal("250.00"),
            )

            result = await broker.place_order(order)

            assert result.order_id == "order-456"
            assert result.status == OrderStatus.PENDING
            assert result.filled_quantity == Decimal("0")

    @pytest.mark.asyncio
    async def test_get_positions(self, broker):
        """Test fetching positions."""
        mock_position = Mock()
        mock_position.symbol = "AAPL"
        mock_position.qty = "100"
        mock_position.avg_entry_price = "145.00"
        mock_position.current_price = "150.00"
        mock_position.market_value = "15000.00"
        mock_position.unrealized_pl = "500.00"

        with patch('src.infrastructure.brokers.alpaca_broker.TradingClient') as mock_client:
            mock_instance = Mock()
            mock_instance.get_all_positions.return_value = [mock_position]
            mock_client.return_value = mock_instance

            await broker.connect()
            positions = await broker.get_positions()

            assert len(positions) == 1
            assert positions[0].symbol == "AAPL"
            assert positions[0].quantity == Decimal("100")
            assert positions[0].side == "long"
            assert positions[0].unrealized_pnl == Decimal("500.00")

    @pytest.mark.asyncio
    async def test_cancel_order(self, broker):
        """Test canceling an order."""
        with patch('src.infrastructure.brokers.alpaca_broker.TradingClient') as mock_client:
            mock_instance = Mock()
            mock_instance.cancel_order_by_id.return_value = None
            mock_client.return_value = mock_instance

            await broker.connect()
            result = await broker.cancel_order("order-123")

            assert result is True
            mock_instance.cancel_order_by_id.assert_called_once_with("order-123")

    @pytest.mark.asyncio
    async def test_get_open_orders(self, broker):
        """Test fetching open orders."""
        mock_order = Mock()
        mock_order.id = "order-789"
        mock_order.symbol = "MSFT"
        mock_order.side.value = "buy"
        mock_order.type.value = "limit"
        mock_order.qty = "10"
        mock_order.filled_qty = "0"
        mock_order.filled_avg_price = None
        mock_order.created_at = datetime.now()
        mock_order.updated_at = None
        mock_order.status.value = "accepted"

        with patch('src.infrastructure.brokers.alpaca_broker.TradingClient') as mock_client:
            mock_instance = Mock()
            mock_instance.get_orders.return_value = [mock_order]
            mock_client.return_value = mock_instance

            await broker.connect()
            orders = await broker.get_open_orders()

            assert len(orders) == 1
            assert orders[0].order_id == "order-789"
            assert orders[0].status == OrderStatus.OPEN
