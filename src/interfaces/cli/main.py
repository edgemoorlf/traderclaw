"""CLI for TraderClaw trading assistant.

Commands:
    import-positions: Import positions from broker CSV export
    advise: Get AI trading advice
    morning-briefing: Get morning briefing on portfolio
    account: View Alpaca account balance
    positions: View current Alpaca positions
    orders: List open orders
    buy: Place a buy order
    sell: Place a sell order
    cancel: Cancel an order
    strategy: Manage and run plain language strategies
"""

import argparse
import asyncio
import os
import sys
from decimal import Decimal
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
from src.application.interfaces.broker import Order, OrderSide, OrderType
from src.infrastructure.brokers import AlpacaBroker
from src.infrastructure.csv_importers import import_positions


def run_strategy_cli(args):
    """Delegate to strategy CLI module."""
    import subprocess
    import sys

    # Pass through to strategy_cli.py
    cmd = [sys.executable, "-m", "src.interfaces.cli.strategy_cli"] + args.strategy_args
    subprocess.run(cmd)


# Global broker instance for trading commands
_broker = None


def get_alpaca_broker(paper: bool = True) -> AlpacaBroker:
    """Get or create Alpaca broker instance."""
    global _broker
    if _broker is None or _broker.paper != paper:
        api_key = os.getenv("ALPACA_API_KEY")
        api_secret = os.getenv("ALPACA_SECRET_KEY")

        if not api_key or not api_secret:
            print("Error: ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in config/.env")
            sys.exit(1)

        _broker = AlpacaBroker(
            api_key=api_key,
            api_secret=api_secret,
            paper=paper
        )
    return _broker


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
        print("Please set it in config/.env or an environment variable")
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


async def cmd_account(args):
    """View Alpaca account balance."""
    broker = get_alpaca_broker(paper=not args.live)

    print(f"🔌 Connecting to Alpaca {'PAPER' if broker.paper else 'LIVE'} trading...")

    try:
        connected = await broker.connect()
        if not connected:
            print("❌ Failed to connect to Alpaca API")
            sys.exit(1)

        balance = await broker.get_account_balance()

        print()
        print("=" * 60)
        print(f"📊 ALPACA {'PAPER' if broker.paper else 'LIVE'} ACCOUNT")
        print("=" * 60)
        print(f"  Cash:           ${balance.cash:>15,.2f}")
        print(f"  Buying Power:   ${balance.buying_power:>15,.2f}")
        print(f"  Equity:         ${balance.equity:>15,.2f}")
        if balance.margin_used:
            print(f"  Margin Used:    ${balance.margin_used:>15,.2f}")
        if balance.margin_available:
            print(f"  Margin Avail:   ${balance.margin_available:>15,.2f}")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


async def cmd_positions(args):
    """View current Alpaca positions."""
    broker = get_alpaca_broker(paper=not args.live)

    print(f"🔌 Connecting to Alpaca {'PAPER' if broker.paper else 'LIVE'} trading...")

    try:
        connected = await broker.connect()
        if not connected:
            print("❌ Failed to connect to Alpaca API")
            sys.exit(1)

        positions = await broker.get_positions()

        if not positions:
            print("\n📭 No open positions")
            return

        print()
        print("=" * 80)
        print(f"📈 OPEN POSITIONS ({len(positions)})")
        print("=" * 80)
        print(f"{'Symbol':<10} {'Qty':>12} {'Avg Entry':>12} {'Current':>12} {'Value':>15} {'P&L':>12}")
        print("-" * 80)

        total_value = 0
        total_pnl = 0

        for pos in positions:
            value = pos.market_value or Decimal("0")
            pnl = pos.unrealized_pnl or Decimal("0")
            total_value += value
            total_pnl += pnl

            print(f"{pos.symbol:<10} {float(pos.quantity):>12.4f} "
                  f"${float(pos.avg_entry_price):>10.2f} ${float(pos.current_price or 0):>10.2f} "
                  f"${float(value):>13.2f} ${float(pnl):>10.2f}")

        print("-" * 80)
        print(f"{'TOTAL':<10} {'':<12} {'':<12} {'':<12} "
              f"${float(total_value):>13.2f} ${float(total_pnl):>10.2f}")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


async def cmd_orders(args):
    """List open orders."""
    broker = get_alpaca_broker(paper=not args.live)

    print(f"🔌 Connecting to Alpaca {'PAPER' if broker.paper else 'LIVE'} trading...")

    try:
        connected = await broker.connect()
        if not connected:
            print("❌ Failed to connect to Alpaca API")
            sys.exit(1)

        orders = await broker.get_open_orders()

        if not orders:
            print("\n📭 No open orders")
            return

        print()
        print("=" * 100)
        print(f"📋 OPEN ORDERS ({len(orders)})")
        print("=" * 100)
        print(f"{'Order ID':<36} {'Symbol':<8} {'Side':<6} {'Type':<10} {'Qty':>10} {'Filled':>10} {'Status':<12}")
        print("-" * 100)

        for order in orders:
            print(f"{order.order_id:<36} {order.symbol:<8} {order.side.value:<6} "
                  f"{order.order_type.value:<10} {float(order.quantity):>10.4f} "
                  f"{float(order.filled_quantity):>10.4f} {order.status.value:<12}")

        print("=" * 100)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


async def cmd_buy(args):
    """Place a buy order."""
    broker = get_alpaca_broker(paper=not args.live)

    # Safety check for live trading
    if not broker.paper and not args.confirm:
        print("⚠️  WARNING: You are about to place a LIVE trade!")
        print(f"   Symbol: {args.symbol}")
        print(f"   Quantity: {args.quantity}")
        print(f"   Type: {args.type}")
        if args.price:
            print(f"   Price: ${args.price}")
        print()
        print("Add --confirm to execute this trade.")
        sys.exit(1)

    print(f"🔌 Connecting to Alpaca {'PAPER' if broker.paper else 'LIVE'} trading...")

    try:
        connected = await broker.connect()
        if not connected:
            print("❌ Failed to connect to Alpaca API")
            sys.exit(1)

        # Parse order type
        order_type_map = {
            "market": OrderType.MARKET,
            "limit": OrderType.LIMIT,
            "stop": OrderType.STOP,
            "stop_limit": OrderType.STOP_LIMIT,
        }
        order_type = order_type_map.get(args.type.lower(), OrderType.MARKET)

        # Create order
        order = Order(
            symbol=args.symbol.upper(),
            side=OrderSide.BUY,
            order_type=order_type,
            quantity=Decimal(str(args.quantity)),
            price=Decimal(str(args.price)) if args.price else None,
            stop_price=Decimal(str(args.stop_price)) if args.stop_price else None,
            time_in_force=args.tif,
            extended_hours=args.extended_hours,
        )

        print(f"\n📤 Placing BUY order...")
        print(f"  Symbol: {order.symbol}")
        print(f"  Quantity: {float(order.quantity)}")
        print(f"  Type: {order.order_type.value}")
        if order.price:
            print(f"  Price: ${float(order.price):.2f}")
        if order.stop_price:
            print(f"  Stop Price: ${float(order.stop_price):.2f}")

        result = await broker.place_order(order)

        print(f"\n✅ Order submitted!")
        print(f"  Order ID: {result.order_id}")
        print(f"  Status: {result.status.value}")
        if result.filled_quantity and result.filled_quantity > 0:
            print(f"  Filled: {float(result.filled_quantity)} @ ${float(result.avg_fill_price) if result.avg_fill_price else 'N/A'}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


async def cmd_sell(args):
    """Place a sell order."""
    broker = get_alpaca_broker(paper=not args.live)

    # Safety check for live trading
    if not broker.paper and not args.confirm:
        print("⚠️  WARNING: You are about to place a LIVE trade!")
        print(f"   Symbol: {args.symbol}")
        print(f"   Quantity: {args.quantity}")
        print(f"   Type: {args.type}")
        if args.price:
            print(f"   Price: ${args.price}")
        print()
        print("Add --confirm to execute this trade.")
        sys.exit(1)

    print(f"🔌 Connecting to Alpaca {'PAPER' if broker.paper else 'LIVE'} trading...")

    try:
        connected = await broker.connect()
        if not connected:
            print("❌ Failed to connect to Alpaca API")
            sys.exit(1)

        # Parse order type
        order_type_map = {
            "market": OrderType.MARKET,
            "limit": OrderType.LIMIT,
            "stop": OrderType.STOP,
            "stop_limit": OrderType.STOP_LIMIT,
        }
        order_type = order_type_map.get(args.type.lower(), OrderType.MARKET)

        # Create order
        order = Order(
            symbol=args.symbol.upper(),
            side=OrderSide.SELL,
            order_type=order_type,
            quantity=Decimal(str(args.quantity)),
            price=Decimal(str(args.price)) if args.price else None,
            stop_price=Decimal(str(args.stop_price)) if args.stop_price else None,
            time_in_force=args.tif,
            extended_hours=args.extended_hours,
        )

        print(f"\n📤 Placing SELL order...")
        print(f"  Symbol: {order.symbol}")
        print(f"  Quantity: {float(order.quantity)}")
        print(f"  Type: {order.order_type.value}")
        if order.price:
            print(f"  Price: ${float(order.price):.2f}")
        if order.stop_price:
            print(f"  Stop Price: ${float(order.stop_price):.2f}")

        result = await broker.place_order(order)

        print(f"\n✅ Order submitted!")
        print(f"  Order ID: {result.order_id}")
        print(f"  Status: {result.status.value}")
        if result.filled_quantity and result.filled_quantity > 0:
            print(f"  Filled: {float(result.filled_quantity)} @ ${float(result.avg_fill_price) if result.avg_fill_price else 'N/A'}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


async def cmd_cancel(args):
    """Cancel an order."""
    broker = get_alpaca_broker(paper=not args.live)

    print(f"🔌 Connecting to Alpaca {'PAPER' if broker.paper else 'LIVE'} trading...")

    try:
        connected = await broker.connect()
        if not connected:
            print("❌ Failed to connect to Alpaca API")
            sys.exit(1)

        result = await broker.cancel_order(args.order_id)

        if result:
            print(f"\n✅ Order {args.order_id} cancelled successfully")
        else:
            print(f"\n❌ Failed to cancel order {args.order_id}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


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

    # account command
    account_parser = subparsers.add_parser(
        "account",
        help="View Alpaca account balance",
    )
    account_parser.add_argument(
        "--live",
        action="store_true",
        help="Use live trading account (default is paper trading)",
    )
    account_parser.set_defaults(func=lambda args: asyncio.run(cmd_account(args)))

    # positions command
    positions_parser = subparsers.add_parser(
        "positions",
        help="View current Alpaca positions",
    )
    positions_parser.add_argument(
        "--live",
        action="store_true",
        help="Use live trading account (default is paper trading)",
    )
    positions_parser.set_defaults(func=lambda args: asyncio.run(cmd_positions(args)))

    # orders command
    orders_parser = subparsers.add_parser(
        "orders",
        help="List open orders",
    )
    orders_parser.add_argument(
        "--live",
        action="store_true",
        help="Use live trading account (default is paper trading)",
    )
    orders_parser.set_defaults(func=lambda args: asyncio.run(cmd_orders(args)))

    # buy command
    buy_parser = subparsers.add_parser(
        "buy",
        help="Place a buy order",
    )
    buy_parser.add_argument(
        "symbol",
        help="Stock symbol (e.g., AAPL)",
    )
    buy_parser.add_argument(
        "quantity",
        type=float,
        help="Quantity to buy (supports fractional shares)",
    )
    buy_parser.add_argument(
        "--type",
        default="market",
        choices=["market", "limit", "stop", "stop_limit"],
        help="Order type (default: market)",
    )
    buy_parser.add_argument(
        "--price",
        type=float,
        help="Limit price (required for limit/stop_limit orders)",
    )
    buy_parser.add_argument(
        "--stop-price",
        type=float,
        help="Stop price (required for stop/stop_limit orders)",
    )
    buy_parser.add_argument(
        "--tif",
        default="day",
        choices=["day", "gtc", "ioc", "fok"],
        help="Time in force (default: day)",
    )
    buy_parser.add_argument(
        "--extended-hours",
        action="store_true",
        help="Allow extended hours trading",
    )
    buy_parser.add_argument(
        "--live",
        action="store_true",
        help="Use live trading (default is paper trading)",
    )
    buy_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm live trade (required for live trading)",
    )
    buy_parser.set_defaults(func=lambda args: asyncio.run(cmd_buy(args)))

    # sell command
    sell_parser = subparsers.add_parser(
        "sell",
        help="Place a sell order",
    )
    sell_parser.add_argument(
        "symbol",
        help="Stock symbol (e.g., AAPL)",
    )
    sell_parser.add_argument(
        "quantity",
        type=float,
        help="Quantity to sell (supports fractional shares)",
    )
    sell_parser.add_argument(
        "--type",
        default="market",
        choices=["market", "limit", "stop", "stop_limit"],
        help="Order type (default: market)",
    )
    sell_parser.add_argument(
        "--price",
        type=float,
        help="Limit price (required for limit/stop_limit orders)",
    )
    sell_parser.add_argument(
        "--stop-price",
        type=float,
        help="Stop price (required for stop/stop_limit orders)",
    )
    sell_parser.add_argument(
        "--tif",
        default="day",
        choices=["day", "gtc", "ioc", "fok"],
        help="Time in force (default: day)",
    )
    sell_parser.add_argument(
        "--extended-hours",
        action="store_true",
        help="Allow extended hours trading",
    )
    sell_parser.add_argument(
        "--live",
        action="store_true",
        help="Use live trading (default is paper trading)",
    )
    sell_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm live trade (required for live trading)",
    )
    sell_parser.set_defaults(func=lambda args: asyncio.run(cmd_sell(args)))

    # cancel command
    cancel_parser = subparsers.add_parser(
        "cancel",
        help="Cancel an order",
    )
    cancel_parser.add_argument(
        "order_id",
        help="Order ID to cancel",
    )
    cancel_parser.add_argument(
        "--live",
        action="store_true",
        help="Use live trading (default is paper trading)",
    )
    cancel_parser.set_defaults(func=lambda args: asyncio.run(cmd_cancel(args)))

    # strategy command - delegates to strategy_cli
    strategy_parser = subparsers.add_parser(
        "strategy",
        help="Manage and run plain language trading strategies",
    )
    strategy_parser.add_argument(
        "strategy_args",
        nargs="*",
        help="Strategy subcommand arguments (try: strategy --help)",
    )
    strategy_parser.set_defaults(func=lambda args: run_strategy_cli(args))

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if hasattr(args, 'func'):
        args.func(args)


if __name__ == "__main__":
    main()
