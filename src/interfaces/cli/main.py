"""CLI for TraderClaw trading assistant.

Commands:
    import-positions: Import positions from broker CSV export
    advise: Get AI trading advice
    morning-briefing: Get morning briefing on portfolio
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables from config/.env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent / "config" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from src.ai import TradingOrchestrator, StrategyModel
from src.infrastructure.csv_importers import import_positions, CSVImporterFactory


def cmd_import_positions(args):
    """Import positions from CSV and display summary."""
    csv_path = args.csv_path

    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    print(f"Importing positions from: {csv_path}")
    print()

    try:
        # Auto-detect broker format
        importer_name = CSVImporterFactory.detect_and_parse.__name__
        positions = import_positions(csv_path)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        sys.exit(1)

    if not positions:
        print("No positions found in CSV.")
        sys.exit(0)

    # Group by account
    by_account = {}
    for pos in positions:
        account = pos.account
        if account not in by_account:
            by_account[account] = []
        by_account[account].append(pos)

    total_value = 0
    total_cost = 0

    print("=" * 70)
    print("IMPORTED POSITIONS")
    print("=" * 70)

    for account, acc_positions in sorted(by_account.items()):
        account_value = sum(p.current_value or 0 for p in acc_positions)
        account_cost = sum(
            (p.avg_cost_basis * p.quantity) if p.avg_cost_basis and p.quantity else 0
            for p in acc_positions
        )
        total_value += account_value
        total_cost += account_cost

        print(f"\n{account} ({acc_positions[0].account_type})")
        print("-" * 50)

        for pos in acc_positions:
            pnl = pos.total_gain_loss_percent
            pnl_str = f"{pnl:+.1f}%" if pnl else "N/A"
            qty = float(pos.quantity) if pos.quantity else 0
            price = float(pos.last_price) if pos.last_price else 0
            print(f"  {pos.symbol:8} | {qty:>10} | ${price:>8.2f} | P&L: {pnl_str:>8}")

    print()
    print("=" * 70)
    print(f"Total Value: ${total_value:,.2f}")
    if total_cost > 0:
        pnl_pct = (total_value - total_cost) / total_cost * 100
        print(f"Cost Basis: ${total_cost:,.2f}")
        print(f"Unrealized P&L: {pnl_pct:+.1f}%")
    print("=" * 70)

    return positions


async def cmd_advise(args):
    """Get AI trading advice on a query."""
    # Check for required API keys
    gemini_key = os.getenv("GEMINI_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")

    if not gemini_key:
        print("Error: GEMINI_API_KEY not set")
        print("Please set it in config/.env or as an environment variable")
        sys.exit(1)

    if not deepseek_key:
        print("Error: DEEPSEEK_API_KEY not set")
        print("Please set it in config/.env or as an environment variable")
        sys.exit(1)

    # Initialize orchestrator
    orchestrator = TradingOrchestrator(
        gemini_api_key=gemini_key,
        strategy_model=StrategyModel.DEEPSEEK,
        strategy_api_key=deepseek_key,
        execution_mode="advisory",
    )

    # Load positions if CSV provided
    if args.csv:
        print(f"Loading positions from: {args.csv}")
        orchestrator.position_service.load_from_csv(args.csv)
        print(f"Loaded positions:\n{orchestrator.position_service.get_positions_summary()}")
        print()

    print(f"Query: {args.query}")
    print()
    print("🤖 Analyzing...")
    print()

    advice = await orchestrator.advise(
        user_id=args.user_id or "cli_user",
        query=args.query,
        symbols=args.symbols,
    )

    print(f"📊 Market Summary: {advice.market_data.market_summary}")
    print()
    print(f"💡 Recommendation: {advice.decision.recommendation}")
    print(f"📈 Confidence: {advice.decision.confidence}")
    print(f"⏱️  Timeframe: {advice.decision.timeframe}")
    print()
    print(f"📝 Analysis:")
    print(f"{advice.decision.rationale}")

    if advice.decision.risks:
        print()
        print("⚠️  Risks:")
        for risk in advice.decision.risks:
            print(f"   - {risk}")


async def cmd_morning_briefing(args):
    """Get morning briefing on portfolio."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")

    if not gemini_key or not deepseek_key:
        print("Error: GEMINI_API_KEY and DEEPSEEK_API_KEY must be set")
        sys.exit(1)

    orchestrator = TradingOrchestrator(
        gemini_api_key=gemini_key,
        strategy_model=StrategyModel.DEEPSEEK,
        strategy_api_key=deepseek_key,
    )

    if args.csv:
        print(f"Loading positions from: {args.csv}")
        orchestrator.position_service.load_from_csv(args.csv)
        print()

    print("🌅 Generating morning briefing...")
    print()

    briefing = await orchestrator.morning_briefing(user_id=args.user_id or "cli_user")

    print(f"📊 Market Summary: {briefing.market_data.market_summary}")
    print()
    print(f"💡 Key Recommendation: {briefing.decision.recommendation}")
    print()
    print(f"📝 Analysis:")
    print(f"{briefing.decision.rationale}")


def main():
    parser = argparse.ArgumentParser(
        description="TraderClaw - AI-powered trading assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # import-positions command
    import_parser = subparsers.add_parser(
        "import-positions",
        help="Import positions from broker CSV export",
    )
    import_parser.add_argument(
        "csv_path",
        help="Path to CSV file from broker (Fidelity, etc.)",
    )
    import_parser.set_defaults(func=cmd_import_positions)

    # advise command
    advise_parser = subparsers.add_parser(
        "advise",
        help="Get AI trading advice",
    )
    advise_parser.add_argument(
        "query",
        help="Your trading question (e.g., 'Should I sell my NVDA?')",
    )
    advise_parser.add_argument(
        "--csv",
        help="Path to CSV file with your positions",
    )
    advise_parser.add_argument(
        "--symbols",
        nargs="+",
        help="Specific symbols to analyze",
    )
    advise_parser.add_argument(
        "--user-id",
        default="cli_user",
        help="User identifier",
    )
    advise_parser.set_defaults(func=lambda args: asyncio.run(cmd_advise(args)))

    # morning-briefing command
    briefing_parser = subparsers.add_parser(
        "morning-briefing",
        help="Get morning briefing on your portfolio",
    )
    briefing_parser.add_argument(
        "--csv",
        help="Path to CSV file with your positions",
    )
    briefing_parser.add_argument(
        "--user-id",
        default="cli_user",
        help="User identifier",
    )
    briefing_parser.set_defaults(func=lambda args: asyncio.run(cmd_morning_briefing(args)))

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if hasattr(args, 'func'):
        args.func(args)


if __name__ == "__main__":
    main()
