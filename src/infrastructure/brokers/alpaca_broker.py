"""Alpaca broker implementation.

Supports both paper trading (default) and live trading.
Paper trading: https://paper-api.alpaca.markets
Live trading: https://api.alpaca.markets

Features:
- Fractional shares
- Extended hours trading
- Real-time market data
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import logging

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
    StopLimitOrderRequest,
    GetOrdersRequest,
)
from alpaca.trading.enums import (
    OrderSide as AlpacaOrderSide,
    OrderType as AlpacaOrderType,
    TimeInForce,
    OrderStatus as AlpacaOrderStatus,
)
from alpaca.common.exceptions import APIError

from ...application.interfaces.broker import (
    AbstractBroker,
    Order,
    OrderResult,
    OrderSide,
    OrderType,
    OrderStatus,
    Position,
    AccountBalance,
)

logger = logging.getLogger(__name__)


class AlpacaBroker(AbstractBroker):
    """Alpaca trading broker.

    Paper trading is enabled by default. Set paper=False for live trading
    with explicit risk acknowledgment.
    """

    PAPER_URL = "https://paper-api.alpaca.markets"
    LIVE_URL = "https://api.alpaca.markets"

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        paper: bool = True,
        config: Optional[dict] = None
    ):
        super().__init__(
            name="alpaca",
            api_key=api_key,
            api_secret=api_secret,
            paper=paper,
            config=config
        )
        self.client: Optional[TradingClient] = None

    async def connect(self) -> bool:
        """Connect to Alpaca API.

        Returns:
            True if connection successful
        """
        if not self.api_key or not self.api_secret:
            logger.error("Alpaca API key and secret are required")
            return False

        try:
            self.client = TradingClient(
                api_key=self.api_key,
                secret_key=self.api_secret,
                paper=self.paper
            )

            # Verify connection by fetching account
            account = self.client.get_account()
            logger.info(
                f"Connected to Alpaca {'paper' if self.paper else 'live'} trading. "
                f"Account: {account.account_number}"
            )
            self._connected = True
            return True

        except APIError as e:
            logger.error(f"Failed to connect to Alpaca: {e}")
            self._connected = False
            return False

    async def get_account_balance(self) -> AccountBalance:
        """Get current account balance.

        Returns:
            AccountBalance with cash, buying power, equity
        """
        if not self._connected:
            raise RuntimeError("Broker not connected. Call connect() first.")

        try:
            account = self.client.get_account()
            return AccountBalance(
                currency="USD",
                cash=Decimal(account.cash),
                buying_power=Decimal(account.buying_power),
                equity=Decimal(account.equity),
                margin_used=Decimal(account.initial_margin) if account.initial_margin else None,
                margin_available=Decimal(account.buying_power) if account.buying_power else None,
            )
        except APIError as e:
            logger.error(f"Failed to get account balance: {e}")
            raise

    async def place_order(self, order: Order) -> OrderResult:
        """Place a new order.

        Supports:
        - Market orders
        - Limit orders
        - Stop orders
        - Stop-limit orders
        - Fractional shares
        - Extended hours

        Args:
            order: Order details

        Returns:
            OrderResult with execution status
        """
        if not self._connected:
            raise RuntimeError("Broker not connected. Call connect() first.")

        # Map internal order type to Alpaca request
        alpaca_side = (
            AlpacaOrderSide.BUY if order.side == OrderSide.BUY else AlpacaOrderSide.SELL
        )

        # Map time in force
        tif_map = {
            "day": TimeInForce.DAY,
            "gtc": TimeInForce.GTC,
            "ioc": TimeInForce.IOC,
            "fok": TimeInForce.FOK,
        }
        tif = tif_map.get(order.time_in_force.lower(), TimeInForce.DAY)

        try:
            if order.order_type == OrderType.MARKET:
                request = MarketOrderRequest(
                    symbol=order.symbol,
                    qty=float(order.quantity),
                    side=alpaca_side,
                    time_in_force=tif,
                    extended_hours=order.extended_hours,
                    client_order_id=order.client_order_id,
                )
            elif order.order_type == OrderType.LIMIT:
                if order.price is None:
                    raise ValueError("Limit orders require a price")
                request = LimitOrderRequest(
                    symbol=order.symbol,
                    qty=float(order.quantity),
                    side=alpaca_side,
                    limit_price=float(order.price),
                    time_in_force=tif,
                    extended_hours=order.extended_hours,
                    client_order_id=order.client_order_id,
                )
            elif order.order_type == OrderType.STOP:
                if order.stop_price is None:
                    raise ValueError("Stop orders require a stop price")
                request = StopOrderRequest(
                    symbol=order.symbol,
                    qty=float(order.quantity),
                    side=alpaca_side,
                    stop_price=float(order.stop_price),
                    time_in_force=tif,
                    extended_hours=order.extended_hours,
                    client_order_id=order.client_order_id,
                )
            elif order.order_type == OrderType.STOP_LIMIT:
                if order.price is None or order.stop_price is None:
                    raise ValueError("Stop-limit orders require both price and stop_price")
                request = StopLimitOrderRequest(
                    symbol=order.symbol,
                    qty=float(order.quantity),
                    side=alpaca_side,
                    limit_price=float(order.price),
                    stop_price=float(order.stop_price),
                    time_in_force=tif,
                    extended_hours=order.extended_hours,
                    client_order_id=order.client_order_id,
                )
            else:
                raise ValueError(f"Unsupported order type: {order.order_type}")

            alpaca_order = self.client.submit_order(request)
            return self._convert_order(alpaca_order)

        except APIError as e:
            logger.error(f"Failed to place order: {e}")
            raise

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order.

        Args:
            order_id: Order to cancel

        Returns:
            True if cancellation successful
        """
        if not self._connected:
            raise RuntimeError("Broker not connected. Call connect() first.")

        try:
            self.client.cancel_order_by_id(order_id)
            return True
        except APIError as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    async def get_order(self, order_id: str) -> Optional[OrderResult]:
        """Get order status by ID.

        Args:
            order_id: Order ID

        Returns:
            OrderResult or None if not found
        """
        if not self._connected:
            raise RuntimeError("Broker not connected. Call connect() first.")

        try:
            alpaca_order = self.client.get_order_by_id(order_id)
            return self._convert_order(alpaca_order)
        except APIError as e:
            logger.error(f"Failed to get order {order_id}: {e}")
            return None

    async def get_positions(self) -> List[Position]:
        """Get all current positions.

        Returns:
            List of Position objects
        """
        if not self._connected:
            raise RuntimeError("Broker not connected. Call connect() first.")

        try:
            alpaca_positions = self.client.get_all_positions()
            return [self._convert_position(p) for p in alpaca_positions]
        except APIError as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol.

        Args:
            symbol: Asset symbol

        Returns:
            Position or None if no position
        """
        if not self._connected:
            raise RuntimeError("Broker not connected. Call connect() first.")

        try:
            alpaca_position = self.client.get_open_position(symbol)
            return self._convert_position(alpaca_position)
        except APIError:
            # Position not found
            return None

    async def get_open_orders(self) -> List[OrderResult]:
        """Get all open orders.

        Returns:
            List of open OrderResult objects
        """
        if not self._connected:
            raise RuntimeError("Broker not connected. Call connect() first.")

        try:
            request = GetOrdersRequest(status="open")
            alpaca_orders = self.client.get_orders(request)
            return [self._convert_order(o) for o in alpaca_orders]
        except APIError as e:
            logger.error(f"Failed to get open orders: {e}")
            return []

    def _convert_order(self, alpaca_order) -> OrderResult:
        """Convert Alpaca order to internal OrderResult."""
        status_map = {
            AlpacaOrderStatus.NEW: OrderStatus.PENDING,
            AlpacaOrderStatus.PENDING_NEW: OrderStatus.PENDING,
            AlpacaOrderStatus.ACCEPTED: OrderStatus.OPEN,
            AlpacaOrderStatus.PARTIALLY_FILLED: OrderStatus.PARTIALLY_FILLED,
            AlpacaOrderStatus.FILLED: OrderStatus.FILLED,
            AlpacaOrderStatus.CANCELED: OrderStatus.CANCELLED,
            AlpacaOrderStatus.DONE_FOR_DAY: OrderStatus.CANCELLED,
            AlpacaOrderStatus.EXPIRED: OrderStatus.CANCELLED,
            AlpacaOrderStatus.REJECTED: OrderStatus.REJECTED,
        }

        side_map = {
            AlpacaOrderSide.BUY: OrderSide.BUY,
            AlpacaOrderSide.SELL: OrderSide.SELL,
        }

        return OrderResult(
            order_id=str(alpaca_order.id),
            status=status_map.get(alpaca_order.status, OrderStatus.REJECTED),
            symbol=alpaca_order.symbol,
            side=side_map.get(alpaca_order.side, OrderSide.BUY),
            order_type=OrderType(alpaca_order.type.value),
            quantity=Decimal(str(alpaca_order.qty)) if alpaca_order.qty else Decimal("0"),
            filled_quantity=Decimal(str(alpaca_order.filled_qty)) if alpaca_order.filled_qty else Decimal("0"),
            avg_fill_price=Decimal(str(alpaca_order.filled_avg_price)) if alpaca_order.filled_avg_price else None,
            created_at=alpaca_order.created_at,
            updated_at=alpaca_order.updated_at,
            broker_message=alpaca_order.status.value if hasattr(alpaca_order.status, 'value') else str(alpaca_order.status),
        )

    def _convert_position(self, alpaca_position) -> Position:
        """Convert Alpaca position to internal Position."""
        qty = Decimal(str(alpaca_position.qty))
        return Position(
            symbol=alpaca_position.symbol,
            quantity=abs(qty),
            avg_entry_price=Decimal(str(alpaca_position.avg_entry_price)),
            current_price=Decimal(str(alpaca_position.current_price)) if alpaca_position.current_price else None,
            market_value=Decimal(str(alpaca_position.market_value)) if alpaca_position.market_value else None,
            unrealized_pnl=Decimal(str(alpaca_position.unrealized_pl)) if alpaca_position.unrealized_pl else None,
            side="long" if qty > 0 else "short",
        )
