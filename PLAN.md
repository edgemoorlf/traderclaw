# TraderClaw Implementation Plan

## Vision

TraderClaw is an **AI-powered autonomous trading agent** that combines large language models with real-time market data to make intelligent trading decisions. Unlike traditional automated systems with rigid rules, TraderClaw understands natural language strategy descriptions, learns from outcomes, and adapts its approach.

---

## Current Status (as of 2026-03-31)

### ✅ Completed

#### AI Infrastructure
- [x] Multi-model orchestration — Gemini (data), DeepSeek / Claude / Qwen (strategy)
- [x] Gemini data agent with Google Search for real-time market data and news
- [x] Strategy agent abstraction with pluggable model backends
- [x] Multi-model consensus engine (weighted, majority, unanimous)
- [x] Trading orchestrator coordinating the full data → decision pipeline
- [x] Language-aware responses (replies in the user's language)

#### Data Layer
- [x] **Polymarket integration** — prediction market sentiment (read-only)
- [x] Yahoo Finance — stock prices and technicals (via `yfinance` + Gemini search)
- [x] CoinGecko — crypto prices (via `pycoingecko` + Gemini search)
- [x] Macro context gathering via Gemini + Google Search
- [x] Position tracking — CSV import from Fidelity

#### Strategy Engine
- [x] Plain language strategy definition (`PlainLanguageStrategy`)
- [x] Strategy execution engine with approval modes (autonomous / hybrid / approval / notify)
- [x] **SQLite persistence** — strategies stored in `data/traderclaw.db`
- [x] Strategy repository with save / load / load_all / delete
- [x] Strategies survive server restarts (loaded from DB on startup)

#### Broker Integration
- [x] **Alpaca** — US stocks, paper trading default / live opt-in
- [x] **OKX** — crypto, demo default / live opt-in
- [x] Abstract broker interface (`AbstractBroker`)
- [x] Multi-account broker manager

#### Interfaces
- [x] **CLI** — import positions, advise, morning briefing, buy/sell/cancel, account/positions/orders
- [x] **Strategy CLI** — create, list, show, delete, run, accounts
- [x] **Web UI** — React + Vite single-screen dashboard
- [x] **FastAPI backend** — REST + WebSocket endpoints
- [x] Portfolio CSV upload via browser
- [x] AI chat interface (natural language → advice / strategy creation)
- [x] Signal approval panel (approve / reject inline)
- [x] Real-time WebSocket updates
- [x] ngrok-compatible (allowedHosts, wss:// support)

#### Infrastructure
- [x] Technical indicators (`technical.py` — RSI, SMA, MACD, Bollinger Bands, etc.)
- [x] CSV importers (Fidelity format)
- [x] SQLite database layer (`src/infrastructure/database.py`)
- [x] Structured logging

---

## In Progress / Next Up

### Notifications
- [ ] Email alerts for significant signals
- [ ] Webhook support (Slack, Discord)
- [ ] Mobile push (via third-party service)

### Strategy Memory & Learning
- [ ] Track which recommendations were approved / rejected
- [ ] Learn user preferences from approval history
- [ ] Adapt confidence thresholds based on feedback
- [ ] Identify implicit rules from user behavior

### Performance Analytics
- [ ] P&L attribution per signal / strategy
- [ ] Decision quality scoring over time
- [ ] Model comparison (DeepSeek vs Claude vs Qwen accuracy)
- [ ] Strategy drift detection

### Additional Data Sources
- [ ] Dedicated Yahoo Finance client module (`src/infrastructure/market_data/yahoo_client.py`)
- [ ] Dedicated CoinGecko client module (`src/infrastructure/market_data/coingecko_client.py`)
- [ ] News aggregation (RSS / API)
- [ ] Social sentiment (optional)

---

## Future Enhancements

### Operations
- [ ] Docker containerization + health checks
- [ ] Graceful shutdown with position reconciliation
- [ ] Decision rate / latency metrics
- [ ] API quota and cost tracking per LLM provider

### Advanced Features
- [ ] **Backtesting** — simulate AI decisions on historical data
- [ ] **Advanced charting** — visual AI decision explanations in web UI
- [ ] **Multi-account support** — manage multiple portfolios
- [ ] **Options strategies** — AI-managed spreads and hedges
- [ ] **Strategy marketplace** — share successful strategies
- [ ] **Voice interface** — natural language via speech
- [ ] **PostgreSQL migration** — when multi-user or cloud deployment needed

---

## Architecture

### Signal Flow
```
CSV / Broker → PositionService → TradingOrchestrator
                                       │
              ┌────────────────────────┤
              ▼                        ▼
     GeminiDataAgent           StrategyAgent
     (market data,             (DeepSeek / Claude
      news, macro)              / Qwen / GPT)
              │                        │
              └────────────┬───────────┘
                           ▼
                    TradingDecision
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       Auto-execute              Approval flow
       (autonomous)           (hybrid / approval)
              │                         │
              └────────────┬────────────┘
                           ▼
                      Broker API
                   (Alpaca / OKX)
```

### Storage
- `data/traderclaw.db` — SQLite, runtime data (strategies, future: signals, audit log)
- `config/.env` — API keys (gitignored)
- `config/brokers.yaml` — broker account configuration

---

## Key Design Principles

1. **AI-First** — strategy expressed in natural language, AI interprets intent
2. **Explainability** — every decision has a human-readable rationale
3. **Gradual trust** — advisory → approval → autonomous, always with emergency stop
4. **Multi-model resilience** — no single LLM dependency, fallback chains
5. **Safety first** — paper trading default, explicit live opt-in, position/loss limits

---

## Risk Acknowledgment

This is an experimental AI-powered trading system. While it includes safety guardrails:

- AI can make mistakes
- Past performance doesn't guarantee future results
- Technical failures can occur
- You are responsible for monitoring and intervention

**Never invest more than you can afford to lose.**
