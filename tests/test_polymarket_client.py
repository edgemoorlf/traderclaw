"""Unit tests for Polymarket client."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import responses

from src.infrastructure.market_data.polymarket_client import PolymarketClient


class TestPolymarketClient:
    """Test Polymarket Gamma API client."""

    @pytest.fixture
    def client(self):
        return PolymarketClient(config={"base_url": "https://gamma-api.polymarket.com"})

    @responses.activate
    @pytest.mark.asyncio
    async def test_connect_success(self, client):
        """Test successful connection."""
        responses.add(
            responses.GET,
            "https://gamma-api.polymarket.com/events",
            json={"events": []},
            status=200
        )
        result = await client.connect()
        assert result is True
        assert client.is_connected() is True

    @responses.activate
    @pytest.mark.asyncio
    async def test_connect_failure(self, client):
        """Test connection failure."""
        responses.add(
            responses.GET,
            "https://gamma-api.polymarket.com/events",
            status=500
        )
        result = await client.connect()
        assert result is False
        assert client.is_connected() is False

    @responses.activate
    @pytest.mark.asyncio
    async def test_get_markets(self, client):
        """Test fetching markets."""
        mock_response = {
            "events": [
                {
                    "slug": "will-it-rain-tomorrow",
                    "title": "Will it rain tomorrow?",
                    "tags": ["weather"],
                    "markets": [
                        {
                            "slug": "will-it-rain-tomorrow-yes",
                            "question": "Will it rain tomorrow?",
                            "description": "Market description",
                            "outcomes": ["Yes", "No"],
                            "outcomePrices": ["0.65", "0.35"],
                            "volume": "100000",
                            "liquidity": "50000",
                            "endDate": "2024-12-31",
                            "clobTokenIds": ["0x123abc"],
                        }
                    ]
                }
            ]
        }
        responses.add(
            responses.GET,
            "https://gamma-api.polymarket.com/events",
            json=mock_response,
            status=200
        )

        markets = await client.get_markets()
        assert len(markets) == 1
        assert markets[0].symbol == "0x123abc"
        assert markets[0].asset_type == "prediction_market"
        assert markets[0].additional_data["outcome_prices"] == ["0.65", "0.35"]

    @responses.activate
    @pytest.mark.asyncio
    async def test_get_current_price(self, client):
        """Test fetching current price."""
        mock_response = {
            "markets": [
                {
                    "outcomePrices": ["0.75", "0.25"]
                }
            ]
        }
        responses.add(
            responses.GET,
            "https://gamma-api.polymarket.com/markets",
            json=mock_response,
            status=200
        )

        price = await client.get_current_price("0x123abc")
        assert price == 0.75

    @responses.activate
    @pytest.mark.asyncio
    async def test_fetch_ohlcv(self, client):
        """Test fetching price history."""
        mock_response = {
            "history": [
                {"timestamp": 1700000000, "price": "0.60"},
                {"timestamp": 1700003600, "price": "0.65"},
            ]
        }
        responses.add(
            responses.GET,
            "https://gamma-api.polymarket.com/prices-history",
            json=mock_response,
            status=200
        )

        data = await client.fetch_ohlcv("0x123abc", limit=2)
        assert len(data) == 2
        assert data[0].close == 0.60
        assert data[1].close == 0.65
        assert data[0].source == "polymarket"

    @responses.activate
    @pytest.mark.asyncio
    async def test_get_event(self, client):
        """Test fetching specific event."""
        mock_response = {
            "slug": "test-event",
            "title": "Test Event",
            "markets": []
        }
        responses.add(
            responses.GET,
            "https://gamma-api.polymarket.com/events/test-event",
            json=mock_response,
            status=200
        )

        event = await client.get_event("test-event")
        assert event["slug"] == "test-event"
        assert event["title"] == "Test Event"
