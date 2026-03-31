"""Strategy CLI commands for TraderClaw.

Commands:
    strategy list: List all strategies
    strategy create: Create a new plain language strategy
    strategy show: Show strategy details
    strategy delete: Delete a strategy
    strategy run: Run a strategy evaluation
    strategy signals: View pending signals
    strategy approve: Approve pending signals
    strategy accounts: Manage broker accounts
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent.parent / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path)

from src.strategies import (
    StrategyExecutionEngine,
    PlainLanguageStrategy,
    StrategyRepository,
    ApprovalMode,
    ConsensusType,
    get_execution_engine,
)
from src.ai import StrategyModel
from src.infrastructure.brokers import get_broker_manager, BrokerAccountConfig


def get_engine() -> StrategyExecutionEngine:
    """Get or create execution engine."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("Error: GEMINI_API_KEY not set in config/.env")
        sys.exit(1)

    # Collect API keys for consensus models
    model_api_keys = {}

    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        model_api_keys["deepseek"] = deepseek_key

    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    if dashscope_key:
        model_api_keys["qwen"] = dashscope_key

    if not model_api_keys:
        print("Error: At least one model API key required (DEEPSEEK_API_KEY or DASHSCOPE_API_KEY)")
        sys.exit(1)

    return get_execution_engine(
        gemini_api_key=gemini_key,
        model_api_keys=model_api_keys,
    )


def cmd_list(args):
    """List all strategies."""
    repo = StrategyRepository()
    strategies = repo.load_all()

    if not strategies:
        print("No strategies found. Create one with: strategy create")
        return

    print("=" * 100)
    print("STRATEGIES")
    print("=" * 100)
    print(f"{'ID':<10} {'Name':<25} {'Symbols':<25} {'Mode':<12} {'Consensus':<10} {'Status'}")
    print("-" * 100)

    for s in strategies:
        symbols_str = ", ".join(s.symbols[:3])
        if len(s.symbols) > 3:
            symbols_str += f" (+{len(s.symbols)-3})"
        symbols_str = symbols_str[:24]

        mode = s.approval_mode.value
        consensus = "yes" if s.use_consensus else "no"
        status = "enabled" if s.enabled else "disabled"

        print(f"{s.id:<10} {s.name:<25} {symbols_str:<25} {mode:<12} {consensus:<10} {status}")

    print("=" * 100)
    print(f"\nTotal: {len(strategies)} strategies")


def cmd_create(args):
    """Create a new strategy."""
    engine = get_engine()

    # Build description from input or use provided
    description = args.description
    if args.interactive:
        print("\n=== Create New Strategy ===")
        print("Describe your trading strategy in plain language:")
        print("(e.g., 'Buy tech stocks when RSI is oversold and news sentiment is positive')")
        print()
        description = input("> ").strip()

        if not description:
            print("Error: Strategy description is required")
            sys.exit(1)

        print("\nEnter symbols to monitor (comma-separated):")
        symbols_input = input("> ").strip()
        symbols = [s.strip().upper() for s in symbols_input.split(",")]
    else:
        symbols = [s.upper() for s in args.symbols]

    # Determine approval mode
    mode_map = {
        "autonomous": ApprovalMode.AUTONOMOUS,
        "hybrid": ApprovalMode.HYBRID,
        "approval": ApprovalMode.APPROVAL,
        "notify": ApprovalMode.NOTIFY,
    }
    approval_mode = mode_map.get(args.mode, ApprovalMode.HYBRID)

    # Determine consensus models
    consensus_models = []
    if args.consensus:
        if "deepseek" in args.consensus:
            consensus_models.append(StrategyModel.DEEPSEEK)
        if "qwen" in args.consensus:
            consensus_models.append(StrategyModel.QWEN)
    if not consensus_models:
        # Default to available models
        if os.getenv("DEEPSEEK_API_KEY"):
            consensus_models.append(StrategyModel.DEEPSEEK)
        if os.getenv("DASHSCOPE_API_KEY"):
            consensus_models.append(StrategyModel.QWEN)

    strategy = engine.create_strategy(
        name=args.name,
        description=description,
        symbols=symbols,
        timeframe=args.timeframe,
        position_sizing=args.position_size or "5% of portfolio per position",
        max_positions=args.max_positions,
        approval_mode=approval_mode,
        auto_execute_confidence_threshold=args.threshold,
        use_consensus=len(consensus_models) > 1,
        consensus_models=consensus_models,
        stop_loss_rule=args.stop_loss,
        take_profit_rule=args.take_profit,
    )

    print(f"\n✅ Strategy created: {strategy.id}")
    print(f"   Name: {strategy.name}")
    print(f"   Symbols: {', '.join(strategy.symbols)}")
    print(f"   Mode: {strategy.approval_mode.value}")
    print(f"   Consensus models: {[m.value for m in strategy.consensus_models]}")


def cmd_show(args):
    """Show strategy details."""
    repo = StrategyRepository()
    strategy = repo.load(args.strategy_id)

    if not strategy:
        print(f"Error: Strategy not found: {args.strategy_id}")
        sys.exit(1)

    print("=" * 70)
    print(f"STRATEGY: {strategy.name}")
    print("=" * 70)
    print(f"ID: {strategy.id}")
    print(f"Status: {'enabled' if strategy.enabled else 'disabled'}")
    print(f"Created: {strategy.created_at.strftime('%Y-%m-%d %H:%M')}")
    print()
    print("DESCRIPTION:")
    print(f"  {strategy.description}")
    print()
    print("CONFIGURATION:")
    print(f"  Symbols: {', '.join(strategy.symbols)}")
    print(f"  Timeframe: {strategy.timeframe}")
    print(f"  Position sizing: {strategy.position_sizing}")
    print(f"  Max positions: {strategy.max_positions}")
    print(f"  Stop loss: {strategy.stop_loss_rule or 'None'}")
    print(f"  Take profit: {strategy.take_profit_rule or 'None'}")
    print()
    print("EXECUTION:")
    print(f"  Approval mode: {strategy.approval_mode.value}")
    print(f"  Auto-execute threshold: {strategy.auto_execute_confidence_threshold}")
    print()
    print("CONSENSUS:")
    print(f"  Use consensus: {strategy.use_consensus}")
    print(f"  Consensus type: {strategy.consensus_type.value}")
    print(f"  Models: {[m.value for m in strategy.consensus_models]}")
    print(f"  Weights: {strategy.model_weights}")
    print("=" * 70)


def cmd_delete(args):
    """Delete a strategy."""
    repo = StrategyRepository()

    if not args.force:
        strategy = repo.load(args.strategy_id)
        if not strategy:
            print(f"Error: Strategy not found: {args.strategy_id}")
            sys.exit(1)

        print(f"Are you sure you want to delete '{strategy.name}'?")
        confirm = input("Type 'yes' to confirm: ").strip()
        if confirm != "yes":
            print("Cancelled")
            return

    success = repo.delete(args.strategy_id)
    if success:
        print(f"✅ Strategy {args.strategy_id} deleted")
    else:
        print(f"❌ Strategy not found: {args.strategy_id}")


async def cmd_run(args):
    """Run strategy evaluation."""
    engine = get_engine()

    # Load strategy
    strategy = engine.repository.load(args.strategy_id)
    if not strategy:
        print(f"Error: Strategy not found: {args.strategy_id}")
        sys.exit(1)

    print(f"🔄 Running strategy: {strategy.name}")
    print(f"   Symbols: {', '.join(strategy.symbols)}")
    print()

    # Load user context from CSV
    from src.ai.orchestrator import PositionService
    position_service = PositionService()
    csv_path = getattr(args, "csv", None)
    if csv_path:
        position_service.load_from_csv(csv_path)
        user_context = asyncio.run(position_service.get_user_context("default"))
    else:
        print("Warning: No --csv provided. Running without portfolio context.")
        user_context = {"total_portfolio_value": 0, "cash_available": 0, "positions": {}}

    # Evaluate strategy
    signals = await engine.evaluate_strategy(
        strategy=strategy,
        user_context=user_context,
        account_id=args.account,
    )

    if not signals:
        print("No signals generated. Strategy returned HOLD for all symbols.")
        return

    print(f"\n📊 Generated {len(signals)} signals:")
    print()

    for signal in signals:
        print("-" * 70)
        print(f"Symbol: {signal.symbol}")
        print(f"Action: {signal.action}")
        print(f"Confidence: {signal.confidence:.2%}")
        print()
        print("Rationale:")
        print(signal.rationale[:300] + "..." if len(signal.rationale) > 300 else signal.rationale)

        if signal.consensus_result:
            print()
            print(f"Consensus agreement: {signal.consensus_result.agreement_level:.2%}")
            print(f"Primary model: {signal.consensus_result.primary_model}")

        # Process signal if not dry-run
        if not args.dry_run:
            plan = await engine.process_signal(signal, strategy, args.account)
            print()
            print(f"Execution plan:")
            print(f"  Approved: {plan.approved}")
            print(f"  Auto-approved: {plan.auto_approved}")
            print(f"  Account: {plan.execution_account}")
            for note in plan.notes:
                print(f"  Note: {note}")

            if plan.approved and signal.executed:
                print(f"  ✅ Executed!")
            elif not plan.approved:
                print(f"  ⏸️  Pending approval")

    print()
    print("=" * 70)
    print(f"Strategy run complete. {len(signals)} signals generated.")


async def cmd_signals(args):
    """View pending signals."""
    # This would require signal persistence, which we haven't implemented yet
    # For now, show a placeholder
    print("Signal persistence not yet implemented.")
    print("Run 'strategy run' to generate and view signals.")


async def cmd_accounts(args):
    """Manage broker accounts."""
    manager = get_broker_manager()

    if args.list:
        accounts = manager.list_accounts()

        if not accounts:
            print("No accounts configured.")
            print("Add one with: strategy accounts --add-paper <name>")
            return

        print("=" * 80)
        print("BROKER ACCOUNTS")
        print("=" * 80)
        print(f"{'ID':<20} {'Name':<20} {'Type':<10} {'Paper':<8} {'Status'}")
        print("-" * 80)

        for acc in accounts:
            status = "enabled" if acc.enabled else "disabled"
            paper = "yes" if acc.paper else "no"
            print(f"{acc.account_id:<20} {acc.name:<20} {acc.broker_type:<10} {paper:<8} {status}")

        print("=" * 80)

    elif args.add_paper:
        # Add paper trading account
        api_key = os.getenv("ALPACA_API_KEY")
        api_secret = os.getenv("ALPACA_SECRET_KEY")

        if not api_key or not api_secret:
            print("Error: ALPACA_API_KEY and ALPACA_SECRET_KEY must be set")
            sys.exit(1)

        account_id = args.add_paper
        name = args.name or account_id

        config = manager.create_paper_account(
            account_id=account_id,
            name=name,
            api_key=api_key,
            api_secret=api_secret,
            metadata={"description": args.description} if args.description else {},
        )

        print(f"✅ Paper account created: {config.account_id}")
        print(f"   Name: {config.name}")
        print(f"   Broker: {config.broker_type}")

    elif args.remove:
        success = manager.remove_account(args.remove)
        if success:
            print(f"✅ Account removed: {args.remove}")
        else:
            print(f"❌ Account not found: {args.remove}")


def main():
    parser = argparse.ArgumentParser(
        description="TraderClaw Strategy Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list command
    list_parser = subparsers.add_parser("list", help="List all strategies")
    list_parser.set_defaults(func=cmd_list)

    # create command
    create_parser = subparsers.add_parser("create", help="Create a new strategy")
    create_parser.add_argument("name", help="Strategy name")
    create_parser.add_argument("--description", "-d", help="Strategy description (plain language)")
    create_parser.add_argument("--symbols", "-s", nargs="+", help="Symbols to monitor")
    create_parser.add_argument("--timeframe", default="1d", help="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)")
    create_parser.add_argument("--mode", default="hybrid",
                               choices=["autonomous", "hybrid", "approval", "notify"],
                               help="Approval mode (default: hybrid)")
    create_parser.add_argument("--threshold", type=float, default=0.8,
                               help="Auto-execute confidence threshold (default: 0.8)")
    create_parser.add_argument("--consensus", nargs="+", choices=["deepseek", "qwen"],
                               help="Models to use for consensus")
    create_parser.add_argument("--position-size", help="Position sizing rule")
    create_parser.add_argument("--max-positions", type=int, default=5, help="Max positions")
    create_parser.add_argument("--stop-loss", help="Stop loss rule")
    create_parser.add_argument("--take-profit", help="Take profit rule")
    create_parser.add_argument("--interactive", "-i", action="store_true",
                               help="Interactive mode")
    create_parser.set_defaults(func=cmd_create)

    # show command
    show_parser = subparsers.add_parser("show", help="Show strategy details")
    show_parser.add_argument("strategy_id", help="Strategy ID")
    show_parser.set_defaults(func=cmd_show)

    # delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a strategy")
    delete_parser.add_argument("strategy_id", help="Strategy ID")
    delete_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    delete_parser.set_defaults(func=cmd_delete)

    # run command
    run_parser = subparsers.add_parser("run", help="Run strategy evaluation")
    run_parser.add_argument("strategy_id", help="Strategy ID")
    run_parser.add_argument("--account", "-a", help="Broker account to use")
    run_parser.add_argument("--csv", help="Path to Fidelity CSV for portfolio context")
    run_parser.add_argument("--dry-run", "-n", action="store_true",
                            help="Generate signals but don't execute")
    run_parser.set_defaults(func=lambda args: asyncio.run(cmd_run(args)))

    # signals command
    signals_parser = subparsers.add_parser("signals", help="View pending signals")
    signals_parser.set_defaults(func=lambda args: asyncio.run(cmd_signals(args)))

    # accounts command
    accounts_parser = subparsers.add_parser("accounts", help="Manage broker accounts")
    accounts_parser.add_argument("--list", "-l", action="store_true", help="List accounts")
    accounts_parser.add_argument("--add-paper", metavar="ID",
                                 help="Add paper trading account with given ID")
    accounts_parser.add_argument("--name", "-n", help="Account name")
    accounts_parser.add_argument("--description", help="Account description")
    accounts_parser.add_argument("--remove", metavar="ID", help="Remove account")
    accounts_parser.set_defaults(func=lambda args: asyncio.run(cmd_accounts(args)))

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if hasattr(args, 'func'):
        args.func(args)


if __name__ == "__main__":
    main()
