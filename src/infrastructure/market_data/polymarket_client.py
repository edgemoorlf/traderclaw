"""Polymarket Gamma API client - READ-ONLY data source.

Uses the Gamma API for market discovery and price data.
NO trading functionality - data source only.

API Docs: https://gamma-api.polymarket.com
"""

from datetime import datetime, timedelta
from typing import List, Optional
import logging

import requests

from ...application.interfaces.market_data_source import (
    MarketDataSource,
    MarketData,
    MarketInfo,
)

logger = logging.getLogger(__name__)


class PolymarketClient(MarketDataSource):
    """Polymarket prediction market data source.

    Provides read-only access to:
    - Event data (questions, descriptions, tags)
    - Market data (outcome prices, volume, liquidity)
    - Historical prices

    Use case: Sentiment analysis, alternative data for strategies.
    NOT for trading - Gamma API is read-only.
    """

    GAMMA_API_URL = "https://gamma-api.polymarket.com"

    def __init__(self, config: Optional[dict] = None):
        super().__init__(name="polymarket", config=config)
        self.base_url = self.config.get("base_url", self.GAMMA_API_URL)
        self.session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    async def connect(self) -> bool:
        """Verify API accessibility.

        Gamma API requires no authentication, so we just verify
        the endpoint is reachable.

        Returns:
            True if API is accessible
        """
        try:
            response = self._session.get(
                f"{self.base_url}/events",
                params={"limit": 1},
                timeout=10
            )
            response.raise_for_status()
            self._connected = True
            logger.info("Polymarket Gamma API connected successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Polymarket API: {e}")
            self._connected = False
            return False

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MarketData]:
        """Fetch historical price data for a Polymarket token.

        Note: Polymarket provides price history, not traditional OHLCV.
        We convert price points to OHLCV format.

        Args:
            symbol: Token ID (e.g., '0x123...' - the clobTokenId)
            timeframe: Not used - Polymarket provides raw price history
            start: Start date
            end: End date
            limit: Maximum data points

        Returns:
            List of MarketData objects
        """
        if not self._connected:
            await self.connect()

        params = {"limit": limit}
        if start:
            params["startDate"] = start.isoformat()
        if end:
            params["endDate"] = end.isoformat()

        try:
            response = self._session.get(
                f"{self.base_url}/prices-history",
                params=params | {"token_id": symbol},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            market_data = []
            for point in data.get("history", []):
                # Polymarket price is 0-1 (probability)
                price = float(point["price"])
                timestamp = datetime.fromtimestamp(point["timestamp"])

                # Create synthetic OHLCV (Polymarket only provides price)
                market_data.append(
                    MarketData(
                        symbol=symbol,
                        timestamp=timestamp,
                        open=price,
                        high=price,
                        low=price,
                        close=price,
                        volume=0,  # Volume not in price history endpoint
                        source="polymarket"
                    )
                )

            return market_data

        except Exception as e:
            logger.error(f"Failed to fetch price history for {symbol}: {e}")
            return []

    async def get_markets(
        self,
        asset_type: Optional[str] = None,
        search: Optional[str] = None,
        active_only: bool = True
    ) -> List[MarketInfo]:
        """List available Polymarket markets.

        Args:
            asset_type: Filter by category (not used for Polymarket)
            search: Search query for market titles
            active_only: Only return active markets

        Returns:
            List of MarketInfo objects
        """
        if not self._connected:
            await self.connect()

        markets = []
        offset = 0
        limit = 100

        while True:
            params = {
                "limit": limit,
                "offset": offset,
                "active": active_only,
                "archived": not active_only,
            }
            if search:
                params["search"] = search

            try:
                response = self._session.get(
                    f"{self.base_url}/events",
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                events = data.get("events", [])
                if not events:
                    break

                for event in events:
                    for market in event.get("markets", []):
                        # Use token_id as symbol if available
                        token_ids = market.get("clobTokenIds", [])
                        symbol = token_ids[0] if token_ids else market.get("slug", "")

                        markets.append(
                            MarketInfo(
                                symbol=symbol,
                                name=market.get("question", event.get("title", "")),
                                asset_type="prediction_market",
                                exchange="polymarket",
                                additional_data={
                                    "event_slug": event.get("slug"),
                                    "market_slug": market.get("slug"),
                                    "description": market.get("description"),
                                    "outcomes": market.get("outcomes"),
                                    "outcome_prices": market.get("outcomePrices"),
                                    "volume": market.get("volume"),
                                    "liquidity": market.get("liquidity"),
                                    "end_date": market.get("endDate"),
                                    "resolution_date": market.get("resolutionDate"),
                                    "tags": event.get("tags", []),
                                }
                            )
                        )

                offset += limit
                if len(events) < limit:
                    break

            except Exception as e:
                logger.error(f"Failed to fetch markets: {e}")
                break

        return markets

    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for a token.

        Args:
            symbol: Token ID (clobTokenId)

        Returns:
            Current price (0-1 probability) or None
        """
        if not self._connected:
            await self.connect()

        try:
            response = self._session.get(
                f"{self.base_url}/markets",
                params={"clobTokenIds": symbol},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            markets = data.get("markets", [])
            if markets:
                prices = markets[0].get("outcomePrices", [])
                if prices:
                    return float(prices[0])  # Yes price

            return None

        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            return None

    async def get_event(self, slug: str) -> Optional[dict]:
        """Get detailed information about a specific event.

        Args:
            slug: Event slug identifier

        Returns:
            Event data dictionary or None
        """
        try:
            response = self._session.get(
                f"{self.base_url}/events/{slug}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get event {slug}: {e}")
            return None

    async def get_market_by_condition_id(self, condition_id: str) -> Optional[dict]:
        """Get market by its condition ID.

        Args:
            condition_id: CTF condition identifier

        Returns:
            Market data dictionary or None
        """
        try:
            response = self._session.get(
                f"{self.base_url}/markets",
                params={"conditionIds": condition_id},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            markets = data.get("markets", [])
            return markets[0] if markets else None
        except Exception as e:
            logger.error(f"Failed to get market {condition_id}: {e}")
            return None
