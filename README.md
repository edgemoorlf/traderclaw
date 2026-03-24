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
│   ├── market_data.yaml        # Data source config
│   ├── brokers.yaml            # Broker settings
│   └── ai_personality.yaml     # AI behavior preferences
├── src/
│   ├── ai/
│   │   ├── llm_client.py       # Claude/Gemini/DeepSeek interface
│   │   ├── strategy_memory.py  # Learns your preferences
│   │   ├── decision_engine.py  # Analyzes and decides
│   │   └── prompt_templates.py # Context assembly
│   ├── application/
│   │   ├── interfaces/         # Abstract base classes
│   │   └── services/           # Core business logic
│   ├── infrastructure/
│   │   ├── market_data/        # Polymarket, Yahoo, etc.
│   │   └── brokers/            # Alpaca, OKX
│   └── interfaces/
│       └── cli.py              # Chat-based interface
├── memory/                     # Conversation history
├── logs/                       # Decision audit trail
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
| **Claude** | Nuanced reasoning, safety | Complex strategy interpretation |
| **Gemini** | Real-time data access | News and sentiment analysis |
| **DeepSeek** | Cost-effective, fast | High-frequency monitoring |

You can use multiple models - e.g., Claude for strategy, Gemini for news analysis.

## License

MIT

---

*TraderClaw: Your AI trading partner that learns how you think.*
