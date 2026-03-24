"""
Example usage of TraderClaw multi-model trading pipeline.

This demonstrates how to use the orchestrator to get trading advice
combining Gemini for data gathering and DeepSeek/Claude for strategy analysis.
"""

import asyncio
import os

try:
    from dotenv import load_dotenv
    load_dotenv("config/.env")
except ImportError:
    pass  # python-dotenv not installed, use env vars directly

from src.ai import (
    TradingOrchestrator,
    StrategyModel,
    GeminiDataAgent,
)


async def example_trading_advice():
    """Example: Get trading advice for a position."""

    # Initialize orchestrator with Gemini + DeepSeek (default)
    orchestrator = TradingOrchestrator(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        strategy_model=StrategyModel.DEEPSEEK,
        strategy_api_key=os.getenv("DEEPSEEK_API_KEY"),
        execution_mode="advisory",  # advisory, approval, or autonomous
    )

    # Example 1: Simple position question
    print("=" * 60)
    print("Example 1: Should I sell AAPL?")
    print("=" * 60)

    advice = await orchestrator.advise(
        user_id="demo_user",
        query="Should I sell my AAPL position? It's up 23% since I bought it.",
    )

    print(f"\nMarket Summary: {advice.market_data.market_summary}")
    print(f"\nRecommendation: {advice.decision.recommendation}")
    print(f"Confidence: {advice.decision.confidence}")
    print(f"\nRationale: {advice.decision.rationale}")
    print(f"\nRisks identified:")
    for risk in advice.decision.risks:
        print(f"  - {risk}")

    if advice.decision.target_price:
        print(f"\nTarget price: ${advice.decision.target_price}")
    if advice.decision.stop_loss:
        print(f"Stop loss: ${advice.decision.stop_loss}")


async def example_with_claude():
    """Example: Use Claude as the strategy model for conservative advice."""

    print("\n" + "=" * 60)
    print("Example 2: Same question with Claude (conservative)")
    print("=" * 60)

    orchestrator = TradingOrchestrator(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        strategy_model=StrategyModel.CLAUDE,
        strategy_api_key=os.getenv("ANTHROPIC_API_KEY"),
        execution_mode="advisory",
    )

    advice = await orchestrator.advise(
        user_id="demo_user",
        query="Should I sell my AAPL position? It's up 23% since I bought it.",
    )

    print(f"\nStrategy Model: Claude")
    print(f"Recommendation: {advice.decision.recommendation}")
    print(f"\nRationale: {advice.decision.rationale}")


async def example_morning_briefing():
    """Example: Generate morning briefing."""

    print("\n" + "=" * 60)
    print("Example 3: Morning Briefing")
    print("=" * 60)

    orchestrator = TradingOrchestrator(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        strategy_model=StrategyModel.DEEPSEEK,
        strategy_api_key=os.getenv("DEEPSEEK_API_KEY"),
    )

    advice = await orchestrator.morning_briefing(user_id="demo_user")

    print(f"\n{advice.market_data.market_summary}")
    print(f"\nKey Recommendations:")
    print(f"  {advice.decision.recommendation}: {advice.decision.rationale}")


async def example_direct_gemini():
    """Example: Use GeminiDataAgent directly for data gathering."""

    print("\n" + "=" * 60)
    print("Example 4: Direct Gemini Data Gathering")
    print("=" * 60)

    agent = GeminiDataAgent(api_key=os.getenv("GEMINI_API_KEY"))

    # Fetch market data for specific symbols
    data = await agent.gather_market_data(
        symbols=["TSLA", "BTC"],
        topics=["EV competition", "Bitcoin ETF flows"]
    )

    print(f"\nMarket Summary: {data.market_summary}")
    print(f"\nTSLA Data:")
    if "TSLA" in data.symbols:
        tsla = data.symbols["TSLA"]
        print(f"  Price: ${tsla.price}")
        print(f"  24h Change: {tsla.change_24h}")
        print(f"  Sentiment: {tsla.sentiment}")
        print(f"  Key News:")
        for news in tsla.key_news[:3]:
            print(f"    - {news}")


async def example_polymarket_signals():
    """Example: Fetch Polymarket prediction market data."""

    print("\n" + "=" * 60)
    print("Example 5: Polymarket Prediction Market Signals")
    print("=" * 60)

    agent = GeminiDataAgent(api_key=os.getenv("GEMINI_API_KEY"))

    signals = await agent.search_polymarket_signals(
        events=["Fed rate decision", "Bitcoin ETF approval", "2024 election"]
    )

    print("\nPrediction Market Signals:")
    for signal in signals[:5]:
        print(f"\n  Event: {signal.get('event', 'N/A')}")
        print(f"  Outcome: {signal.get('outcome', 'N/A')}")
        print(f"  Probability: {signal.get('probability', 'N/A')}")
        print(f"  Volume (24h): {signal.get('volume_24h', 'N/A')}")
        print(f"  Trend: {signal.get('trend', 'N/A')}")


def main():
    """Run all examples."""
    print("TraderClaw Multi-Model Trading Pipeline Examples")
    print("=" * 60)

    # Check for required API keys
    if not os.getenv("GEMINI_API_KEY"):
        print("\nERROR: GEMINI_API_KEY not found in config/.env")
        print("Please set up your API keys first:")
        print("  1. cp config/.env.example config/.env")
        print("  2. Edit config/.env with your API keys")
        return

    # Run examples
    try:
        asyncio.run(example_trading_advice())
        # asyncio.run(example_with_claude())
        # asyncio.run(example_morning_briefing())
        # asyncio.run(example_direct_gemini())
        # asyncio.run(example_polymarket_signals())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
