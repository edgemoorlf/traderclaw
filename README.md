# TraderClaw

An **AI-powered autonomous trading agent** that makes intelligent trading decisions using large language models (DeepSeek, Gemini, Claude), personal strategy insights, and real-time market data including prediction market sentiment from Polymarket.

## Overview

TraderClaw is not a traditional automated trading system with rigid technical indicators. Instead, it's an **AI trader** that:

- **Understands your strategy** through natural language conversations
- **Analyzes markets** using LLMs with access to real-time data and news
- **Monitors your positions** 24/7 and identifies opportunities or risks
- **Incorporates sentiment** from prediction markets (Polymarket) and social signals
- **Operates with your permission** - from fully autonomous to approval-required modes
- **Learns and adapts** based on outcomes and your feedback

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        TRADERCLAW AI AGENT                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Your       │    │   Public     │    │  Prediction  │      │
│  │  Insights    │ +  │ Market Data  │ +  │  Markets     │      │
│  │ & Strategies │    │  & News      │    │ (Polymarket) │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             ▼                                   │
│              ┌─────────────────────────────┐                   │
│              │    LLM Analysis Engine      │                   │
│              │  (Claude / Gemini / DeepSeek)│                  │
│              └─────────────────────────────┘                   │
│                             │                                   │
│                             ▼                                   │
│              ┌─────────────────────────────┐                   │
│              │    Trading Decision         │                   │
│              │  - Should we trade?         │                   │
│              │  - What action?             │                   │
│              │  - Position sizing?         │                   │
│              │  - Risk assessment?         │                   │
│              └─────────────────────────────┘                   │
│                             │                                   │
│              ┌──────────────┼──────────────┐                   │
│              ▼              ▼              ▼                   │
│        ┌─────────┐   ┌──────────┐   ┌──────────┐              │
│        │  Auto   │   │  Suggest │   │  Notify  │              │
│        │ Execute │   │  Approval│   │  Only    │              │
│        └─────────┘   └──────────┘   └──────────┘              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Concepts

### 1. AI Strategy Understanding

Instead of coding rules, you **describe your trading philosophy** to the AI:

> *"I'm bullish on tech stocks when sentiment is positive but fear is high. I like to scale in gradually when VIX spikes above 25."

> *"For crypto, I follow smart money flows. When prediction markets show high conviction on economic outcomes, I take the other side if the price hasn't moved yet."

The AI interprets these insights and applies them to real-time decisions.

### 2. Multi-Modal Intelligence

The AI combines:
- **Technical analysis** - Price action, volume, indicators (traditional)
- **Fundamental analysis** - Earnings, macro data, sector trends
- **Sentiment analysis** - Polymarket predictions, social media, news
- **Position context** - Your current exposure, P&L, risk limits
- **Market microstructure** - Order book depth, funding rates, flows

### 3. Operational Modes

| Mode | Description | Best For |
|------|-------------|----------|
| **Autonomous** | AI executes trades within defined guardrails | Experienced traders with clear strategies |
| **Approval** | AI proposes, you approve each trade | Learning to trust the system |
| **Advisory** | AI suggests, you manually execute | Research and validation phase |
| **Monitoring** | AI watches and alerts only | Hands-off oversight |

## Data Sources

| Source | Type | Purpose |
|--------|------|---------|
| **Polymarket** | Prediction markets | Sentiment, event probabilities, contrarian signals |
| **Yahoo Finance** | Stock data | Price, fundamentals, news |
| **CoinGecko** | Crypto data | Prices, volumes, on-chain metrics |
| **News APIs** | Real-time news | Event detection, sentiment shifts |
| **Social Signals** | Social media | Crowd sentiment, trending topics |

## Supported Brokers

| Broker | Asset Class | Mode |
|--------|-------------|------|
| **Alpaca** | US Stocks | Paper (default) / Live |
| **OKX** | Crypto | Demo (default) / Live |

## Portfolio Import

TraderClaw can import your existing positions from broker CSV exports:

| Broker | Export Path | Status |
|--------|-------------|--------|
| **Fidelity** | Positions page → Download CSV | ✅ Supported |
| Schwab | Coming soon | 🚧 Planned |
| E*Trade | Coming soon | 🚧 Planned |

### Fidelity CSV Import

1. Log into Fidelity.com
2. Go to your Portfolio → Positions
3. Click "Download" to export CSV
4. Import with: `python -m src.interfaces.cli.main import-positions positions.csv`

The system will automatically:
- Parse all accounts (Individual, IRA, ROTH IRA, etc.)
- Extract symbols, quantities, cost basis, and P&L
- Clean symbol names (remove "COM", "CL A" suffixes)
- Calculate total portfolio value and unrealized gains/losses

### Installation

```bash
# Clone and setup
git clone <repo-url>
cd traderclaw

# Install dependencies (using uv recommended)
uv pip install -r requirements.txt

# Or with pip
pip install -r requirements.txt
```

### Configuration

```bash
# Copy example environment file
cp config/.env.example config/.env

# Edit config/.env with your API keys:
# - GEMINI_API_KEY (for data gathering with Google Search)
# - DEEPSEEK_API_KEY (for strategy analysis)
# - ALPACA_API_KEY / ALPACA_SECRET_KEY (for stock trading)
# - OKX_API_KEY / OKX_API_SECRET / OKX_PASSPHRASE (for crypto trading)
```

### CLI Usage

TraderClaw provides a command-line interface for importing positions and getting AI trading advice.

#### 1. Import Your Portfolio

Export positions from your broker (Fidelity, etc.) and import:

```bash
# Import from Fidelity CSV export
uv run python -m src.interfaces.cli.main import-positions path/to/positions.csv

# Example output:
# ==================================================================
# IMPORTED POSITIONS
# ==================================================================
# ROTH IRA (ROTH_IRA)
# --------------------------------------------------
#   NVDA     |      180.0 | $  175.64 | P&L:  +127.8%
#   TSLA     |      120.0 | $  380.85 | P&L:   +20.0%
#   ...
# ==================================================================
# Total Value: $279,898.52
```

#### 2. Get AI Trading Advice

```bash
# Ask about specific positions
uv run python -m src.interfaces.cli.main advise "Should I take profits on NVDA?" \
    --csv path/to/positions.csv

# Specify symbols explicitly
uv run python -m src.interfaces.cli.main advise "Is Bitcoin looking bullish?" \
    --csv path/to/positions.csv \
    --symbols BTC ETH
```

#### 3. Morning Briefing

```bash
# Get a comprehensive briefing on your portfolio
uv run python -m src.interfaces.cli.main morning-briefing \
    --csv path/to/positions.csv
```

---

### Strategy Management (New)

TraderClaw now supports **plain language strategies** that the AI interprets and executes. No coding required—just describe your trading philosophy in natural language.

#### Create a Strategy

```bash
# Create a simple strategy
uv run python -m src.interfaces.cli.main strategy create my_strategy \
    --description "Buy tech stocks when RSI is oversold and sentiment is positive" \
    --symbols AAPL MSFT NVDA \
    --mode hybrid

# Interactive mode (recommended for complex strategies)
uv run python -m src.interfaces.cli.main strategy create my_strategy -i
```

**Approval Modes:**
- `autonomous` - AI executes trades automatically within guardrails
- `hybrid` - Auto-execute high-confidence signals, ask for approval on others
- `approval` - Every trade requires your explicit approval
- `notify` - AI suggests trades, you execute manually

#### List and Manage Strategies

```bash
# List all strategies
uv run python -m src.interfaces.cli.main strategy list

# View strategy details
uv run python -m src.interfaces.cli.main strategy show <strategy_id>

# Delete a strategy
uv run python -m src.interfaces.cli.main strategy delete <strategy_id>
```

#### Run a Strategy

```bash
# Dry run - generate signals without executing
uv run python -m src.interfaces.cli.main strategy run <strategy_id> --dry-run

# Run with specific account
uv run python -m src.interfaces.cli.main strategy run <strategy_id> \
    --account my_paper_account
```

#### Manage Broker Accounts

```bash
# List configured accounts
uv run python -m src.interfaces.cli.main strategy accounts --list

# Add a paper trading account
uv run python -m src.interfaces.cli.main strategy accounts \
    --add-paper my_paper_account \
    --name "My Paper Trading"

# Remove an account
uv run python -m src.interfaces.cli.main strategy accounts --remove <account_id>
```

#### Example: Complete Strategy Workflow

```bash
# 1. Add a paper trading account
uv run python -m src.interfaces.cli.main strategy accounts \
    --add-paper tech_strategy_paper \
    --name "Tech Strategy Paper Account"

# 2. Create a strategy
uv run python -m src.interfaces.cli.main strategy create tech_momentum \
    --description "Buy oversold tech stocks (RSI < 30) with positive news sentiment. Position size: 5% per trade. Max 3 positions." \
    --symbols AAPL MSFT NVDA GOOGL \
    --mode hybrid \
    --threshold 0.85 \
    --max-positions 3

# 3. Run the strategy (dry run first)
uv run python -m src.interfaces.cli.main strategy run tech_momentum --dry-run

# 4. Run live (paper trading)
uv run python -m src.interfaces.cli.main strategy run tech_momentum \
    --account tech_strategy_paper
```

---

### Web UI (New)

TraderClaw now includes a modern web interface for non-technical users. The Web UI provides a single-screen dashboard where you can manage positions, create strategies using natural language, and approve trading signals.

#### Starting the Web UI

```bash
# 1. Install frontend dependencies
cd web
npm install

# 2. Start the frontend dev server
npm run dev

# 3. In another terminal, start the backend API
uv run python -m src.interfaces.web.main
```

Then open `http://localhost:3000` in your browser.

#### Web UI Features

**Single-Screen Dashboard:**
- **Portfolio Overview** - Total value, daily changes, all positions
- **Position Management** - Click any position to see details, P&L, and active strategies
- **AI Chat Interface** - Type natural language commands like "Sell 50% of NVDA at $800"
- **Signal Approval** - Review and approve trading signals inline
- **Real-time Updates** - WebSocket connection for live price and signal updates

**Creating Strategies in Web UI:**
1. Click on a position to expand it
2. Click "+ Add Exit Strategy" or type in the AI chat
3. Describe your strategy in plain English
4. Review the AI's interpretation
5. Confirm to activate

**Example Commands:**
- "Sell half my NVDA when it hits $800"
- "Set a trailing stop of 10% on AAPL"
- "If TSLA drops below $300, sell everything"
- "Trim NVDA to 20% of my portfolio"

#### Web UI Architecture

```
web/
├── src/
│   ├── components/
│   │   ├── PositionList.tsx    # Position display with expand/collapse
│   │   ├── AIChat.tsx          # Natural language chat interface
│   │   ├── AlertPanel.tsx      # Signals and alerts
│   │   └── Header.tsx          # Portfolio summary header
│   ├── App.tsx                 # Main dashboard layout
│   └── types.ts                # TypeScript interfaces
├── package.json
└── vite.config.ts
```

Backend API endpoints (FastAPI):
- `GET /api/portfolio` - Portfolio with positions
- `POST /api/strategies/parse` - Preview strategy from natural language
- `POST /api/strategies` - Create confirmed strategy
- `GET /api/signals/pending` - Signals awaiting approval
- `WS /ws` - Real-time WebSocket updates

### Python API Usage

For programmatic access:

```python
import asyncio
import os
from src.ai import TradingOrchestrator, StrategyModel

async def main():
    # Initialize the orchestrator
    orchestrator = TradingOrchestrator(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        strategy_model=StrategyModel.DEEPSEEK,
        strategy_api_key=os.getenv("DEEPSEEK_API_KEY"),
        execution_mode="advisory",  # advisory, approval, or autonomous
    )

    # Load your positions from CSV
    portfolio = orchestrator.position_service.load_from_csv("positions.csv")
    print(f"Loaded portfolio: ${portfolio['total_portfolio_value']:,.2f}")

    # Get AI advice
    advice = await orchestrator.advise(
        user_id="user_123",
        query="Should I sell my NVDA position? It's up 127%",
        symbols=["NVDA"]
    )

    print(f"Recommendation: {advice.decision.recommendation}")
    print(f"Confidence: {advice.decision.confidence}")
    print(f"Rationale: {advice.decision.rationale}")

asyncio.run(main())
```

### Running Modes

| Mode | Command | Description |
|------|---------|-------------|
| **Advisory** | (default) | AI suggests, you manually execute |
| **Approval** | Set in code | AI proposes, you approve each trade |
| **Autonomous** | Set in code | AI executes within defined guardrails |

## Example Interactions

### Daily Morning Briefing
```
🤖 TraderClaw: Good morning! Here's your market briefing:

Positions: AAPL +2.3%, TSLA -1.1%, BTC +5.4%

Key Signals:
• Polymarket shows 78% conviction on Fed pause next week
• AAPL approaching your target zone ($185-190)
• BTC funding rates turning negative (potential squeeze)

Suggestion: Trim 50% of AAPL position, add to BTC if it breaks $43k
Risk: Moderate | Confidence: High

[Approve] [Modify] [Skip] [Explain More]
```

### Real-Time Alert
```
🤖 TraderClaw: Position Alert!

Your TSLA position is down 4% in 30 minutes.
• News: Battery supplier issue reported
• Polymarket EV sentiment dropping 15 points
• Your stop rule: "Cut losses at -5% on bad news"

Recommendation: Close position (-4.2% realized loss)
Alternative: Hedge with QQQ puts

[Execute] [Hold] [Set Alert at -5%] [Explain]
```

### Strategy Refinement
```
You: "I want to be more aggressive when VIX is above 30"

🤖 TraderClaw: Understood. I'll adjust the strategy:
• Current: Max 5% position size
• VIX > 30: Increase to 10% with tighter stops
• VIX > 40: Consider inverse ETFs, reduce long exposure

This aligns with your previous insight about volatility opportunities.
Confirm these changes? [Yes] [Adjust] [Cancel]
```

## Project Structure

```
traderclaw/
├── config/
│   ├── .env                    # API keys (gitignored)
│   ├── .env.example            # Example environment file
│   ├── strategies.yaml         # Strategy storage
│   └── brokers.yaml            # Multi-account broker settings
├── src/
│   ├── ai/
│   │   ├── llm_client.py       # DeepSeek/Gemini/Qwen interface
│   │   ├── trading_orchestrator.py  # Main trading coordination
│   │   └── models.py           # AI model enums and configs
│   ├── strategies/
│   │   ├── execution_engine.py # Plain language strategy engine
│   │   └── consensus.py        # Multi-model consensus
│   ├── indicators/
│   │   └── technical.py        # Technical indicator calculations
│   ├── application/
│   │   ├── interfaces/         # Abstract base classes
│   │   │   ├── broker.py       # Broker interface
│   │   │   └── market_data_source.py
│   │   └── services/
│   │       └── position_service.py  # Portfolio management
│   ├── infrastructure/
│   │   ├── market_data/        # Data clients
│   │   │   ├── yahoo_client.py
│   │   │   ├── coingecko_client.py
│   │   │   └── polymarket_client.py
│   │   └── brokers/            # Broker implementations
│   │       ├── alpaca_broker.py
│   │       ├── okx_broker.py
│   │       └── broker_manager.py  # Multi-account support
│   └── interfaces/
│       └── cli/
│           ├── main.py         # Main CLI entry point
│           └── strategy_cli.py # Strategy management commands
├── data/
│   └── imported_positions/     # Saved portfolio snapshots
└── tests/
```

## Safety & Guardrails

- **Paper trading default**: All new strategies start in simulation
- **Position limits**: AI respects max position sizes you define
- **Loss limits**: Daily/weekly loss circuit breakers
- **Explainability**: Every trade includes reasoning you can review
- **Audit trail**: Complete log of all AI decisions and rationales
- **Emergency stop**: Instant halt via CLI or mobile notification

## AI Model Recommendations

| Model | Strengths | Best For |
|-------|-----------|----------|
| **DeepSeek** | Cost-effective, fast, strong reasoning | Primary strategy analysis |
| **Gemini** | Real-time data access via Google Search | News and market data gathering |
| **Qwen (DashScope)** | Fast, good for consensus | Multi-model validation |

**Multi-Model Consensus**: TraderClaw supports running multiple models simultaneously for higher-confidence decisions. When enabled, DeepSeek and Qwen both analyze the strategy, and their signals are combined for consensus.

You can configure models in your `.env`:
```bash
# Required
GEMINI_API_KEY=your_gemini_key

# For strategy execution (at least one)
DEEPSEEK_API_KEY=your_deepseek_key
DASHSCOPE_API_KEY=your_qwen_key
```

## License

MIT

---

*TraderClaw: Your AI trading partner that learns how you think.*
