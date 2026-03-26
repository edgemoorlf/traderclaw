"""Technical indicators for strategy analysis.

This module provides indicator calculations that can be fed to LLMs
along with plain language strategy descriptions.
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Dict, Any
import statistics

import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class IndicatorValues:
    """Technical indicator values for a symbol."""
    symbol: str
    price: float
    price_change_1d: float
    price_change_5d: float
    volume: int
    volume_ratio: float  # vs 20-day average
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    rsi_14: Optional[float] = None
    rsi_7: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_position: Optional[float] = None  # 0-1 position within bands
    atr_14: Optional[float] = None  # Average True Range


def calculate_sma(prices: List[float], period: int) -> Optional[float]:
    """Calculate Simple Moving Average."""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """Calculate Relative Strength Index."""
    if len(prices) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    # Use last 'period' values
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_bollinger_bands(
    prices: List[float],
    period: int = 20,
    std_dev: float = 2.0
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Calculate Bollinger Bands (upper, middle, lower)."""
    if len(prices) < period:
        return None, None, None

    sma = calculate_sma(prices, period)
    recent_prices = prices[-period:]
    std = statistics.stdev(recent_prices)

    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)

    # Position within bands (0 = lower, 1 = upper, 0.5 = middle)
    position = (prices[-1] - lower) / (upper - lower) if upper != lower else 0.5

    return upper, sma, lower, position


def calculate_macd(
    prices: List[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> tuple[Optional[float], Optional[float]]:
    """Calculate MACD and signal line."""
    if len(prices) < slow + signal:
        return None, None

    # Calculate EMAs
    def ema(data: List[float], period: int) -> float:
        multiplier = 2 / (period + 1)
        ema_value = sum(data[:period]) / period
        for price in data[period:]:
            ema_value = (price * multiplier) + (ema_value * (1 - multiplier))
        return ema_value

    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)

    macd = ema_fast - ema_slow

    # Signal line is EMA of MACD
    # Simplified: calculate approximate signal
    signal_line = macd * 0.9  # Approximation

    return macd, signal_line


def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Optional[float]:
    """Calculate Average True Range."""
    if len(closes) < period + 1:
        return None

    true_ranges = []
    for i in range(1, len(closes)):
        high = highs[i] if i < len(highs) else closes[i]
        low = lows[i] if i < len(lows) else closes[i]
        prev_close = closes[i-1]

        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)

        true_ranges.append(max(tr1, tr2, tr3))

    if len(true_ranges) < period:
        return None

    return sum(true_ranges[-period:]) / period


class IndicatorCalculator:
    """Calculate technical indicators for symbols."""

    def __init__(self, cache: Optional[Dict] = None):
        self.cache = cache or {}

    def fetch_price_data(self, symbol: str, period: str = "3mo") -> Dict[str, List[float]]:
        """Fetch historical price data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            if hist.empty:
                logger.warning(f"No data returned for {symbol}")
                return {}

            return {
                "prices": hist["Close"].tolist(),
                "volumes": hist["Volume"].tolist(),
                "highs": hist["High"].tolist(),
                "lows": hist["Low"].tolist(),
            }
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            return {}

    def calculate_all(self, symbol: str) -> Optional[IndicatorValues]:
        """Calculate all indicators for a symbol."""
        data = self.fetch_price_data(symbol)

        if not data or not data.get("prices"):
            return None

        prices = data["prices"]
        volumes = data["volumes"]
        highs = data.get("highs", [])
        lows = data.get("lows", [])

        current_price = prices[-1]
        prev_price = prices[-2] if len(prices) > 1 else current_price

        # Calculate volume ratio vs 20-day average
        volume_ratio = 1.0
        if len(volumes) >= 20:
            avg_volume = sum(volumes[-20:]) / 20
            current_volume = volumes[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        # Calculate Bollinger Bands
        bb_upper, sma_20, bb_lower, bb_pos = calculate_bollinger_bands(prices)

        return IndicatorValues(
            symbol=symbol,
            price=current_price,
            price_change_1d=((current_price - prev_price) / prev_price * 100) if prev_price else 0,
            price_change_5d=((current_price - prices[-5]) / prices[-5] * 100) if len(prices) >= 5 else 0,
            volume=volumes[-1],
            volume_ratio=volume_ratio,
            sma_20=sma_20,
            sma_50=calculate_sma(prices, 50),
            sma_200=calculate_sma(prices, 200),
            rsi_14=calculate_rsi(prices, 14),
            rsi_7=calculate_rsi(prices, 7),
            macd=calculate_macd(prices)[0],
            macd_signal=calculate_macd(prices)[1],
            bb_upper=bb_upper,
            bb_lower=bb_lower,
            bb_position=bb_pos,
            atr_14=calculate_atr(highs, lows, prices, 14) if highs and lows else None,
        )

    def format_for_llm(self, indicators: IndicatorValues) -> str:
        """Format indicators as natural language for LLM consumption."""
        lines = [
            f"Technical Analysis for {indicators.symbol}:",
            f"  Current Price: ${indicators.price:.2f}",
            f"  1-Day Change: {indicators.price_change_1d:+.2f}%",
            f"  5-Day Change: {indicators.price_change_5d:+.2f}%",
            "",
            "Trend Indicators:",
        ]

        if indicators.sma_20:
            above_sma20 = "above" if indicators.price > indicators.sma_20 else "below"
            lines.append(f"  20-day SMA: ${indicators.sma_20:.2f} (price is {above_sma20})")

        if indicators.sma_50:
            above_sma50 = "above" if indicators.price > indicators.sma_50 else "below"
            lines.append(f"  50-day SMA: ${indicators.sma_50:.2f} (price is {above_sma50})")

        if indicators.sma_200:
            above_sma200 = "above" if indicators.price > indicators.sma_200 else "below"
            trend = "bullish" if indicators.price > indicators.sma_200 else "bearish"
            lines.append(f"  200-day SMA: ${indicators.sma_200:.2f} (long-term trend: {trend})")

        lines.append("")
        lines.append("Momentum Indicators:")

        if indicators.rsi_14:
            rsi_desc = "overbought" if indicators.rsi_14 > 70 else "oversold" if indicators.rsi_14 < 30 else "neutral"
            lines.append(f"  RSI(14): {indicators.rsi_14:.1f} ({rsi_desc})")

        if indicators.rsi_7:
            lines.append(f"  RSI(7): {indicators.rsi_7:.1f} (short-term)")

        if indicators.macd and indicators.macd_signal:
            macd_signal = "bullish" if indicators.macd > indicators.macd_signal else "bearish"
            lines.append(f"  MACD: {indicators.macd:.3f} (signal: {macd_signal})")

        lines.append("")
        lines.append("Volatility & Volume:")

        if indicators.bb_position is not None:
            bb_desc = "upper band (overbought)" if indicators.bb_position > 0.8 else "lower band (oversold)" if indicators.bb_position < 0.2 else "middle"
            lines.append(f"  Bollinger Bands: {indicators.bb_position*100:.0f}% ({bb_desc})")

        vol_desc = "above average" if indicators.volume_ratio > 1.5 else "below average" if indicators.volume_ratio < 0.8 else "normal"
        lines.append(f"  Volume: {indicators.volume_ratio:.1f}x average ({vol_desc})")

        if indicators.atr_14:
            lines.append(f"  ATR(14): ${indicators.atr_14:.2f} (average daily range)")

        return "\n".join(lines)


# Singleton instance
_indicator_calculator: Optional[IndicatorCalculator] = None


def get_indicator_calculator() -> IndicatorCalculator:
    """Get singleton indicator calculator."""
    global _indicator_calculator
    if _indicator_calculator is None:
        _indicator_calculator = IndicatorCalculator()
    return _indicator_calculator
