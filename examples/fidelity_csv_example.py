"""
Example: Using Fidelity CSV import with multi-model trading advice.

This demonstrates how to:
1. Import positions from Fidelity CSV export
2. Get AI trading advice on specific positions
3. Get morning briefing on entire portfolio
"""

import asyncio
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv("config/.env")
except ImportError:
    pass

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ai import TradingOrchestrator, StrategyModel
from src.infrastructure.csv_importers import FidelityCSVImporter


async def example_load_and_advise():
    """
    Load positions from Fidelity CSV and get trading advice.
    """
    csv_path = "examples/positions_03-23-2026.csv"

    # Check if file exists
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        print("Please place your Fidelity export in examples/positions_03-23-2026.csv")
        return

    # Step 1: Import positions from Fidelity CSV
    print("=" * 70)
    print("Step 1: Importing positions from Fidelity CSV")
    print("=" * 70)

    importer = FidelityCSVImporter()
    positions = importer.parse(csv_path)

    print(f"\nImported {len(positions)} positions:\n")

    # Group by account
    by_account = {}
    for pos in positions:
        account = pos.account
        if account not in by_account:
            by_account[account] = []
        by_account[account].append(pos)

    for account, account_positions in by_account.items():
        print(f"\n{account} ({account_positions[0].account_type}):")
        print("-" * 50)
        for pos in account_positions[:5]:  # Show first 5
            pnl = f"{pos.total_gain_loss_percent:+.1f}%" if pos.total_gain_loss_percent else "N/A"
            print(f"  {pos.symbol:6} | {pos.quantity:>8} shares | "
                  f"${pos.last_price:>8} | P&L: {pnl:>8}")
        if len(account_positions) > 5:
            print(f"  ... and {len(account_positions) - 5} more positions")

    # Step 2: Initialize orchestrator with CSV-loaded positions
    print("\n" + "=" * 70)
    print("Step 2: Initializing Trading Orchestrator")
    print("=" * 70)

    orchestrator = TradingOrchestrator(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        strategy_model=StrategyModel.DEEPSEEK,
        strategy_api_key=os.getenv("DEEPSEEK_API_KEY"),
        execution_mode="advisory",
    )

    # Load positions into the orchestrator
    portfolio = orchestrator.position_service.load_from_csv(csv_path)

    print(f"\nPortfolio loaded:")
    print(f"  Total Value: ${portfolio['total_portfolio_value']:,.2f}")
    print(f"  Unrealized P&L: {portfolio['unrealized_pnl_pct']:+.1f}%")
    print(f"  Positions: {len(portfolio['positions'])}")

    # Step 3: Get advice on specific position
    print("\n" + "=" * 70)
    print("Step 3: Analyzing NVDA position")
    print("=" * 70)

    if "NVDA" in portfolio["positions"]:
        nvda = portfolio["positions"]["NVDA"]
        print(f"\nYour NVDA position:")
        print(f"  Quantity: {nvda['quantity']} shares")
        print(f"  Entry Price: ${nvda['avg_entry_price']:.2f}")
        print(f"  Current Price: ${nvda['current_price']:.2f}")
        print(f"  Unrealized P&L: {nvda['unrealized_pnl_pct']:+.1f}%")

        print("\n🤖 Getting AI analysis...")

        advice = await orchestrator.advise(
            user_id="fidelity_user",
            query="Should I take profits on my NVDA position? It's up 127%",
            symbols=["NVDA"]
        )

        print(f"\n📊 Market Summary: {advice.market_data.market_summary}")
        print(f"\n💡 Recommendation: {advice.decision.recommendation}")
        print(f"📈 Confidence: {advice.decision.confidence}")
        print(f"\n📝 Rationale:\n{advice.decision.rationale}")

        if advice.decision.risks:
            print(f"\n⚠️  Risks:")
            for risk in advice.decision.risks:
                print(f"   - {risk}")
    else:
        print("NVDA not found in portfolio. Let's analyze another position...")

    # Step 4: Morning briefing on entire portfolio
    print("\n" + "=" * 70)
    print("Step 4: Morning Briefing on Full Portfolio")
    print("=" * 70)

    print("\n🤖 Generating morning briefing...")

    briefing = await orchestrator.morning_briefing(user_id="fidelity_user")

    print(f"\n📊 Market Summary: {briefing.market_data.market_summary}")
    print(f"\n💡 Key Recommendation: {briefing.decision.recommendation}")
    print(f"📝 Analysis:\n{briefing.decision.rationale}")


async def example_single_position_query():
    """
    Example: Ask about a specific position without specifying details.
    """
    csv_path = "examples/positions_03-23-2026.csv"

    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        return

    print("=" * 70)
    print("Example: Natural query with auto-loaded positions")
    print("=" * 70)

    orchestrator = TradingOrchestrator(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        strategy_model=StrategyModel.DEEPSEEK,
        strategy_api_key=os.getenv("DEEPSEEK_API_KEY"),
    )

    # Load positions
    orchestrator.position_service.load_from_csv(csv_path)

    # Just ask - system knows your positions automatically
    queries = [
        "Should I sell my TSLA?",
        "Is COIN a good hold right now?",
        "What's my worst performing position?",
    ]

    for query in queries[:2]:  # Just show first 2
        print(f"\n🙋 User: {query}")
        print("\n🤖 Analyzing...")

        advice = await orchestrator.advise(
            user_id="fidelity_user",
            query=query
        )

        print(f"\n💡 {advice.decision.recommendation}")
        print(f"📝 {advice.decision.rationale[:200]}...")
        print("-" * 50)


def main():
    """Run examples."""
    print("TraderClaw Fidelity CSV Import Example")
    print("=" * 70)
    print()

    # Check for required API keys
    required = ["GEMINI_API_KEY", "DEEPSEEK_API_KEY"]
    missing = [k for k in required if not os.getenv(k)]

    if missing:
        print("❌ Missing API keys:")
        for key in missing:
            print(f"   - {key}")
        print("\nPlease set these in config/.env")
        return

    print("✅ API keys configured")

    # Run examples
    try:
        asyncio.run(example_load_and_advise())
        # asyncio.run(example_single_position_query())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
