"""Gemini Data Agent - Fetches fresh market data via Google Search.

This module uses Gemini with Google Search capabilities to gather
real-time market data, news, and sentiment for the trading pipeline.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


@dataclass
class SymbolData:
    """Market data for a single symbol."""
    symbol: str
    price: Optional[float]
    change_24h: Optional[str]
    change_1h: Optional[str]
    key_news: List[str]
    upcoming_events: List[str]
    sentiment: str
    source_url: Optional[str] = None


@dataclass
class MacroContext:
    """Broader market conditions."""
    vix: Optional[float]
    fed_policy: str
    market_regime: str  # "risk_on", "risk_off", "mixed"
    sector_performance: Dict[str, str]
    major_events: List[str]


@dataclass
class MarketDataPackage:
    """Complete data package for strategy model."""
    timestamp: datetime
    market_summary: str
    symbols: Dict[str, SymbolData]
    macro: Optional[MacroContext]
    polymarket_signals: List[Dict[str, Any]]
    data_sources: List[str]


class GeminiDataAgent:
    """
    Uses Gemini with Google Search to fetch fresh market data.

    This agent is responsible for the "Data Intelligence" layer
    of the trading pipeline. It gathers real-time information
    that the strategy model will analyze.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        """
        Initialize the Gemini Data Agent.

        Args:
            api_key: Google AI Studio API key
            model_name: Gemini model to use (must support search)
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

        logger.info(f"GeminiDataAgent initialized with model: {model_name}")

    async def gather_market_data(
        self,
        symbols: List[str],
        topics: Optional[List[str]] = None
    ) -> MarketDataPackage:
        """
        Gather comprehensive market data for given symbols.

        Uses Gemini with Google Search to find:
        - Current prices and changes
        - Recent news
        - Upcoming events
        - Market sentiment

        Args:
            symbols: List of stock/crypto tickers
            topics: Additional topics to research

        Returns:
            MarketDataPackage with structured data
        """
        if not symbols:
            raise ValueError("At least one symbol required")

        logger.info(f"Gathering market data for: {symbols}")

        # Build comprehensive search prompt
        search_prompt = self._build_search_prompt(symbols, topics)

        try:
            # Call Gemini with search tool
            response = await self._generate_with_search(search_prompt)

            # Parse structured output
            data = self._parse_market_data_response(response, symbols)

            logger.info(f"Successfully gathered data for {len(data.symbols)} symbols")
            return data

        except Exception as e:
            logger.error(f"Failed to gather market data: {e}")
            # Return minimal package on error
            return self._create_error_package(symbols, str(e))

    async def search_polymarket_signals(
        self,
        events: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Search for prediction market data on Polymarket.

        Args:
            events: Event keywords to search for

        Returns:
            List of Polymarket signal dictionaries
        """
        if not events:
            return []

        logger.info(f"Searching Polymarket for: {events}")

        prompt = f"""Search Polymarket prediction markets for these events/topics:
{chr(10).join(f"- {e}" for e in events)}

For each relevant market found, extract:
- Event name/title
- Current probability/odds (as percentage)
- Trading volume (24h)
- Recent price movement (trending up/down)
- Any notable trading activity

If the event has multiple outcomes, list the top 2-3.

Output as JSON list:
[
  {{
    "event": "event name",
    "outcome": "Yes/No/Specific outcome",
    "probability": 0.75,
    "volume_24h": "$1.2M",
    "trend": "up/down/stable",
    "notes": "any notable activity"
  }}
]"""

        try:
            response = await self._generate_with_search(prompt)
            return self._parse_polymarket_response(response)
        except Exception as e:
            logger.error(f"Failed to fetch Polymarket data: {e}")
            return []

    async def get_macro_context(self) -> Optional[MacroContext]:
        """
        Get broader market conditions and macro context.

        Returns:
            MacroContext with VIX, Fed policy, market regime, etc.
        """
        logger.info("Fetching macro context")

        prompt = """Search for current macro market conditions:

1. VIX index (fear gauge) - current level and trend
2. Fed policy - recent statements, rate expectations
3. Market regime - risk-on or risk-off environment
4. Sector performance - which sectors leading/lagging
5. Major events today/this week that could move markets

Output as JSON:
{
  "vix": 16.5,
  "vix_trend": "low/stable",
  "fed_policy": "pause expected, rate cuts in Q2",
  "market_regime": "risk_on",
  "sector_performance": {
    "tech": "leading +2%",
    "energy": "lagging -1%",
    "financials": "stable"
  },
  "major_events": ["Fed Chair speech at 2pm", "CPI data Thursday"]
}"""

        try:
            response = await self._generate_with_search(prompt)
            return self._parse_macro_response(response)
        except Exception as e:
            logger.error(f"Failed to fetch macro context: {e}")
            return None

    async def _generate_with_search(self, prompt: str) -> str:
        """
        Generate content with Google Search enabled.

        Args:
            prompt: The search prompt

        Returns:
            Generated text response
        """
        # Use the search tool - new SDK format
        google_search_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[google_search_tool],
                temperature=0.1,
                top_p=0.95,
                top_k=40,
                max_output_tokens=4096,
            ),
        )

        return response.text

    def _build_search_prompt(
        self,
        symbols: List[str],
        topics: Optional[List[str]]
    ) -> str:
        """Build comprehensive search prompt for market data."""

        symbols_str = ", ".join(symbols)
        topics_str = ", ".join(topics) if topics else "general market sentiment"

        return f"""Search for current market information.

Symbols to research: {symbols_str}
Additional topics: {topics_str}

For each symbol, find the following information:
1. Current trading price
2. Price change in last 24 hours (percentage)
3. Price change in last 1 hour (if available)
4. Key news headlines from today affecting this symbol
5. Any upcoming events (earnings, product launches, FDA decisions, etc.)
6. Overall market sentiment (bullish, bearish, or neutral)

Also provide:
- A brief summary of overall market conditions
- Any major macro events that could affect these positions

Format your response as valid JSON:
{{
  "market_summary": "Brief 1-2 sentence market overview",
  "symbols": {{
    "SYMBOL1": {{
      "price": 185.50,
      "change_24h": "+2.3%",
      "change_1h": "+0.5%",
      "key_news": ["Headline 1", "Headline 2"],
      "upcoming_events": ["Earnings on March 28"],
      "sentiment": "bullish"
    }},
    "SYMBOL2": {{...}}
  }}
}}

Be precise with numbers. If data is not available, use null."""

    def _parse_market_data_response(
        self,
        response: str,
        requested_symbols: List[str]
    ) -> MarketDataPackage:
        """Parse Gemini response into structured MarketDataPackage."""

        try:
            # Extract JSON from response (in case there's extra text)
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            symbols_data = {}
            for symbol in requested_symbols:
                symbol_upper = symbol.upper()
                raw = data.get("symbols", {}).get(symbol_upper, {})

                symbols_data[symbol_upper] = SymbolData(
                    symbol=symbol_upper,
                    price=raw.get("price"),
                    change_24h=raw.get("change_24h"),
                    change_1h=raw.get("change_1h"),
                    key_news=raw.get("key_news", []),
                    upcoming_events=raw.get("upcoming_events", []),
                    sentiment=raw.get("sentiment", "neutral"),
                )

            return MarketDataPackage(
                timestamp=datetime.utcnow(),
                market_summary=data.get("market_summary", "No summary available"),
                symbols=symbols_data,
                macro=None,  # Fetched separately
                polymarket_signals=[],  # Fetched separately
                data_sources=["google_search"],
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response}")
            return self._create_error_package(requested_symbols, "Parse error")

    def _parse_polymarket_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse Polymarket search response."""
        try:
            json_str = self._extract_json(response)
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse Polymarket data: {e}")
            return []

    def _parse_macro_response(self, response: str) -> Optional[MacroContext]:
        """Parse macro context response."""
        try:
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            return MacroContext(
                vix=data.get("vix"),
                fed_policy=data.get("fed_policy", "Unknown"),
                market_regime=data.get("market_regime", "unknown"),
                sector_performance=data.get("sector_performance", {}),
                major_events=data.get("major_events", []),
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse macro context: {e}")
            return None

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that might contain markdown or extra content."""
        # Handle None or empty text
        if not text:
            return "{}"

        # Try to find JSON in code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()

        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()

        # Try to find JSON between curly braces
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start:end+1]

        # Try to find JSON array
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            return text[start:end+1]

        return text.strip()

    def _create_error_package(
        self,
        symbols: List[str],
        error: str
    ) -> MarketDataPackage:
        """Create minimal package when data fetch fails."""
        return MarketDataPackage(
            timestamp=datetime.utcnow(),
            market_summary=f"Error fetching data: {error}",
            symbols={
                s.upper(): SymbolData(
                    symbol=s.upper(),
                    price=None,
                    change_24h=None,
                    change_1h=None,
                    key_news=[],
                    upcoming_events=[],
                    sentiment="unknown",
                )
                for s in symbols
            },
            macro=None,
            polymarket_signals=[],
            data_sources=[],
        )
