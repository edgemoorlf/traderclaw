"""Abstract interface for market data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class MarketData:
    """Standardized market data structure."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str


@dataclass
class MarketInfo:
    """Market metadata structure."""
    symbol: str
    name: str
    asset_type: str  # 'stock', 'crypto', 'prediction_market', etc.
    exchange: Optional[str] = None
    additional_data: Optional[dict] = None


class MarketDataSource(ABC):
    """Abstract base class for all market data sources.

    Implementations: YahooFinanceClient, CoinGeckoClient, PolymarketClient
    """

    def __init__(self, name: str, config: Optional[dict] = None):
        self.name = name
        self.config = config or {}
        self._connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Initialize connection to the data source.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MarketData]:
        """Fetch OHLCV (Open, High, Low, Close, Volume) data.

        Args:
            symbol: Market symbol (e.g., 'AAPL', 'BTC-USD', 'POLY-EVENT-123')
            timeframe: Data granularity ('1m', '5m', '1h', '1d', etc.)
            start: Start date/time
            end: End date/time
            limit: Maximum number of data points

        Returns:
            List of MarketData objects
        """
        pass

    @abstractmethod
    async def get_markets(
        self,
        asset_type: Optional[str] = None,
        search: Optional[str] = None,
        active_only: bool = True
    ) -> List[MarketInfo]:
        """List available markets.

        Args:
            asset_type: Filter by asset type
            search: Search query string
            active_only: Only return actively trading markets

        Returns:
            List of MarketInfo objects
        """
        pass

    @abstractmethod
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current/latest price for a symbol.

        Args:
            symbol: Market symbol

        Returns:
            Current price or None if unavailable
        """
        pass

    async def health_check(self) -> bool:
        """Check if data source is accessible and healthy.

        Returns:
            True if healthy
        """
        try:
            await self.connect()
            return self._connected
        except Exception:
            return False

    def is_connected(self) -> bool:
        """Check current connection status."""
        return self._connected
