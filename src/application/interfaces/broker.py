"""Abstract interface for trading brokers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """Order request structure."""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None  # Required for limit orders
    stop_price: Optional[Decimal] = None  # Required for stop orders
    time_in_force: str = "day"  # 'day', 'gtc', 'ioc', 'fok'
    extended_hours: bool = False
    client_order_id: Optional[str] = None


@dataclass
class OrderResult:
    """Order execution result."""
    order_id: str
    status: OrderStatus
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    filled_quantity: Decimal
    avg_fill_price: Optional[Decimal]
    created_at: datetime
    updated_at: Optional[datetime] = None
    broker_message: Optional[str] = None


@dataclass
class Position:
    """Current position in an asset."""
    symbol: str
    quantity: Decimal
    avg_entry_price: Decimal
    current_price: Optional[Decimal]
    market_value: Optional[Decimal]
    unrealized_pnl: Optional[Decimal]
    side: str  # 'long' or 'short'


@dataclass
class AccountBalance:
    """Account balance information."""
    currency: str
    cash: Decimal
    buying_power: Decimal
    equity: Decimal
    margin_used: Optional[Decimal] = None
    margin_available: Optional[Decimal] = None


class AbstractBroker(ABC):
    """Abstract base class for all trading brokers.

    Implementations: AlpacaBroker, OKXBroker

    Safety-first design:
    - Paper/sandbox trading by default
    - Explicit opt-in required for live trading
    - No accidental live trades
    """

    def __init__(
        self,
        name: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        paper: bool = True,  # Default to paper trading
        config: Optional[dict] = None
    ):
        self.name = name
        self.api_key = api_key
        self.api_secret = api_secret
        self.paper = paper  # True = paper/sandbox, False = live
        self.config = config or {}
        self._connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the broker API.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def get_account_balance(self) -> AccountBalance:
        """Get current account balance.

        Returns:
            AccountBalance with cash, buying power, equity
        """
        pass

    @abstractmethod
    async def place_order(self, order: Order) -> OrderResult:
        """Place a new order.

        Args:
            order: Order details

        Returns:
            OrderResult with execution status
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order.

        Args:
            order_id: Order to cancel

        Returns:
            True if cancellation successful
        """
        pass

    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[OrderResult]:
        """Get order status by ID.

        Args:
            order_id: Order ID

        Returns:
            OrderResult or None if not found
        """
        pass

    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all current positions.

        Returns:
            List of Position objects
        """
        pass

    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol.

        Args:
            symbol: Asset symbol

        Returns:
            Position or None if no position
        """
        pass

    @abstractmethod
    async def get_open_orders(self) -> List[OrderResult]:
        """Get all open orders.

        Returns:
            List of open OrderResult objects
        """
        pass

    def is_paper(self) -> bool:
        """Check if broker is in paper/sandbox mode."""
        return self.paper

    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected

    async def health_check(self) -> bool:
        """Check if broker API is accessible."""
        try:
            await self.connect()
            return self._connected
        except Exception:
            return False
