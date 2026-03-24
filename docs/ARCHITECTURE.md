# TraderClaw Context Assembly Architecture

## Core Principle

The LLM receives a **curated, structured snapshot** of relevant data - not raw feeds. The system acts as an intelligent filter, assembling only what matters for the trading decision at hand.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONTEXT ASSEMBLY PIPELINE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│   │   Raw Data   │  │   Raw Data   │  │   Raw Data   │  │   Raw Data   │   │
│   │   Sources    │  │   Sources    │  │   Sources    │  │   Sources    │   │
│   │              │  │              │  │              │  │              │   │
│   │ • Polymarket │  │ • Alpaca     │  │ • News APIs  │  │ • On-chain   │   │
│   │ • Yahoo      │  │ • OKX        │  │ • Twitter    │  │ • Fed data   │   │
│   │ • CoinGecko  │  │ • WebSocket  │  │ • Earnings   │  │ • Macro      │   │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│          │                 │                 │                 │            │
│          └─────────────────┼─────────────────┼─────────────────┘            │
│                            ▼                 ▼                              │
│                 ┌─────────────────────────────────────┐                     │
│                 │      INTELLIGENT DATA LAYER          │                     │
│                 │                                      │                     │
│                 │  ┌─────────────┐  ┌───────────────┐ │                     │
│                 │  │   Cache     │  │   Relevance   │ │                     │
│                 │  │   Manager   │──▶│    Engine     │ │                     │
│                 │  │             │  │               │ │                     │
│                 │  │ • Time-boxed│  │ • Signal      │ │                     │
│                 │  │ • Volatility│  │   detection   │ │                     │
│                 │  │ • Event     │  │ • Noise       │ │                     │
│                 │  │   driven    │  │   filtering   │ │                     │
│                 │  └─────────────┘  └───────────────┘ │                     │
│                 └──────────────────┬──────────────────┘                     │
│                                    ▼                                        │
│                 ┌─────────────────────────────────────┐                     │
│                 │      CONTEXT BUILDER                │                     │
│                 │                                     │                     │
│                 │  Assembles structured snapshot:     │                     │
│                 │  • Market snapshot (prices, trends) │                     │
│                 │  • Sentiment layer (predictions)    │                     │
│                 │  • Position context (your exposure) │                     │
│                 │  • Event horizon (upcoming catalysts)│                    │
│                 │  • Risk indicators (volatility, correlation)│              │
│                 └──────────────────┬──────────────────┘                     │
│                                    ▼                                        │
│                 ┌─────────────────────────────────────┐                     │
│                 │      LLM OPTIMIZED OUTPUT           │                     │
│                 │                                     │                     │
│                 │  Hierarchical, prioritized context  │                     │
│                 │  with confidence scores and sources │                     │
│                 └─────────────────────────────────────┘                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Source Architecture

### 1. Real-Time Data Streams (WebSocket)

**Purpose**: Prices that change every second
**Update Frequency**: Real-time
**Cache Strategy**: 1-second sliding window

```python
@dataclass
class PriceTick:
    symbol: str
    price: float
    bid: float
    ask: float
    volume_24h: float
    timestamp: datetime
    source: str  # "alpaca", "okx", "polymarket"
    change_1h: float
    change_24h: float
```

### 2. Microstructure Data (Order Book)

**Purpose**: Market depth, liquidity, flow
**Update Frequency**: 5-10 seconds
**Cache Strategy**: 30-second retention

```python
@dataclass
class MarketMicrostructure:
    symbol: str
    spread_pct: float
    bid_depth: float  # USD value at bid
    ask_depth: float  # USD value at ask
    imbalance: float  # -1.0 to 1.0 (sell to buy pressure)
    large_orders: List[Dict]  # Notable block orders
    funding_rate: Optional[float]  # For perps
    open_interest: Optional[float]
```

### 3. Sentiment Layer (Polymarket + Social)

**Purpose**: Crowd wisdom and narrative detection
**Update Frequency**: 1-5 minutes
**Cache Strategy**: 5-minute TTL

```python
@dataclass
class SentimentSnapshot:
    timestamp: datetime

    # Prediction markets (ground truth probabilities)
    polymarket: Dict[str, PolymarketSignal]

    # Social sentiment (if enabled)
    social: Optional[SocialSentiment]

    # News flow
    news: NewsDigest

    # Aggregate sentiment score
    overall_bullish_pct: float  # 0-100
    fear_greed_index: int  # 0-100

@dataclass
class PolymarketSignal:
    event_slug: str
    event_title: str
    yes_price: float  # 0-1 probability
    volume_24h: float
    liquidity: float
    confidence: str  # "high", "medium", "low" based on volume
    related_assets: List[str]  # Which tickers this affects
    trading_implication: str  # Generated insight
```

### 4. Position & Portfolio Context

**Purpose**: What you currently hold and P&L
**Update Frequency**: Real-time (synced with brokers)
**Cache Strategy**: Always fresh

```python
@dataclass
class PortfolioSnapshot:
    timestamp: datetime
    total_value: float
    cash_usd: float
    buying_power: float
    margin_used: Optional[float]

    positions: List[PositionContext]

    # Risk metrics
    concentration_risk: Dict[str, float]  # Max position %
    sector_exposure: Dict[str, float]
    beta_to_spy: float
    var_95_daily: float  # Value at risk

    # Performance
    total_return_pct: float
    day_pnl: float
    unrealized_pnl: float

@dataclass
class PositionContext:
    symbol: str
    asset_type: str  # "stock", "crypto"
    quantity: float
    avg_entry: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float

    # AI-enriched context
    days_held: int
    distance_to_target: Optional[float]  # If target price set
    distance_to_stop: Optional[float]  # If stop loss set
    correlation_to_portfolio: float  # How it moves with rest of portfolio
    related_polymarket_events: List[str]  # Which predictions affect this
```

### 5. Event Horizon (Upcoming Catalysts)

**Purpose**: Known future events that will move markets
**Update Frequency**: Hourly
**Cache Strategy**: 1-hour TTL

```python
@dataclass
class EventHorizon:
    timestamp: datetime

    # Next 24 hours
    next_24h: List[MarketEvent]

    # Next week
    next_week: List[MarketEvent]

    # Earnings calendar for held positions
    earnings_coming: List[EarningsEvent]

    # Fed/events
    fed_meetings: List[FedEvent]

@dataclass
class MarketEvent:
    datetime: datetime
    title: str
    importance: str  # "high", "medium", "low"
    affected_assets: List[str]
    expected_impact: str  # AI-generated
    historical_volatility: Optional[float]  # How much market moved historically
```

### 6. Macro & Market Regime

**Purpose**: Big picture context
**Update Frequency**: Daily
**Cache Strategy**: 4-hour TTL

```python
@dataclass
class MacroContext:
    timestamp: datetime

    # Rates
    fed_funds_rate: float
    treasury_10y: float
    treasury_2y: float
    yield_curve_inverted: bool

    # Credit conditions
    vix: float
    credit_spreads: float  # High yield spread
    dxy: float  # Dollar index

    # Market regime
    regime: str  # "risk_on", "risk_off", "transition", "uncertain"
    trend_spy: str  # "uptrend", "downtrend", "sideways"
    trend_qqq: str
    trend_btc: str

    # AI summary
    regime_summary: str  # "Risk-on environment supported by..."
```

## Context Assembly Pipeline

### Step 1: Data Collection

```python
class DataCollector:
    """Collects from all sources with optimal frequencies."""

    async def collect_for_decision(
        self,
        symbols: List[str],
        decision_type: str  # "trade_opportunity", "risk_check", "morning_brief"
    ) -> RawDataBundle:
        """
        Fetches only relevant data for this decision type.
        Parallel async requests to minimize latency.
        """
        tasks = [
            self.get_prices(symbols),  # WebSocket or REST
            self.get_polymarket_signals(symbols),  # Related events
            self.get_positions(),  # Current holdings
            self.get_news(symbols, lookback_hours=24),
            self.get_macro() if decision_type == "morning_brief" else None,
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self.merge_results(results)
```

### Step 2: Relevance Engine

```python
class RelevanceEngine:
    """Filters noise, amplifies signals."""

    def score_news_item(self, item: NewsItem, holdings: List[str]) -> float:
        """
        Score 0-100 based on:
        - Direct mention of held positions (100)
        - Sector relevance (70)
        - Market-moving potential (keyword analysis)
        - Source credibility
        """

    def detect_significant_price_move(
        self,
        tick: PriceTick,
        threshold_pct: float = 2.0
    ) -> bool:
        """
        Detect if price move is significant enough to note.
        Considers:
        - Absolute % change
        - Volume vs average
        - Time of day (news hours vs quiet)
        - Asset volatility (BTC 5% vs SPY 1%)
        """

    def rank_polymarket_signals(
        self,
        signals: List[PolymarketSignal],
        portfolio: PortfolioSnapshot
    ) -> List[PolymarketSignal]:
        """
        Prioritize signals affecting held positions.
        High volume + price divergence = top priority.
        """
```

### Step 3: Context Builder

```python
class ContextBuilder:
    """Assembles final LLM context."""

    def build_trading_context(
        self,
        raw_data: RawDataBundle,
        user_strategy: str,
        max_tokens: int = 8000
    ) -> TradingContext:
        """
        Builds hierarchical context optimized for LLM consumption.

        Priority order (most important first):
        1. Your positions & P&L (always relevant)
        2. Price action on held assets (immediate concern)
        3. Prediction market signals (your edge)
        4. News affecting your positions (risk management)
        5. Market regime & macro (context)
        6. Other opportunities (if capacity allows)
        """

        return TradingContext(
            snapshot_time=datetime.utcnow(),
            portfolio=self.format_portfolio(raw_data.positions),
            alerts=self.format_alerts(raw_data),
            market_snapshot=self.format_market_snapshot(raw_data.prices),
            sentiment=self.format_sentiment(raw_data.polymarket),
            events=self.format_events(raw_data.events),
            macro=self.format_macro(raw_data.macro) if raw_data.macro else None,
            strategy_reminder=user_strategy,
        )

    def format_alerts(self, data: RawDataBundle) -> List[str]:
        """
        Generate human-readable alerts for significant events.
        Examples:
        - "ALERT: AAPL down 3% on high volume"
        - "ALERT: Polymarket shows 80% confidence in Fed pause (you're long TLT)"
        - "ALERT: BTC funding rate highly negative (potential squeeze)"
        """
```

## LLM-Optimized Output Format

### Trading Decision Context

```json
{
  "metadata": {
    "snapshot_time": "2026-03-23T14:32:00Z",
    "data_freshness": "<30s",
    "context_version": "1.0"
  },

  "your_portfolio": {
    "total_value": "$152,430",
    "day_pnl": "+$1,240 (+0.8%)",
    "buying_power": "$45,000",

    "positions": [
      {
        "symbol": "AAPL",
        "qty": 100,
        "avg_entry": "$150",
        "current": "$185.50",
        "pnl": "+23.7%",
        "value": "$18,550",
        "alerts": ["Up 2.3% today", "Near your target $190"],
        "related_polymarket": "Consumer spending predictions: 65% bullish"
      },
      {
        "symbol": "BTC",
        "qty": 0.5,
        "avg_entry": "$40,000",
        "current": "$67,890",
        "pnl": "+69.7%",
        "value": "$33,945",
        "alerts": ["Funding rate -0.01% (bearish, potential squeeze)"],
        "related_polymarket": "ETF approval odds: 82% by June"
      }
    ],

    "risk_flags": [
      "AAPL is 12% of portfolio (concentrated)",
      "Tech exposure: 45% (high correlation risk)"
    ]
  },

  "market_snapshot": {
    "spy": {"price": 512.34, "change": "+0.4%", "trend": "uptrend"},
    "qqq": {"price": 445.12, "change": "+0.6%", "trend": "uptrend"},
    "vix": 16.5,
    "regime": "Risk-on, low volatility"
  },

  "sentiment_intelligence": {
    "polymarket_high_confidence": [
      {
        "event": "Fed Pause March",
        "probability": 78,
        "confidence": "high",
        "volume_24h": "$2.4M",
        "implication": "Bonds likely rally if correct",
        "affects_your": ["TLT"]
      }
    ],
    "divergence_alerts": [
      {
        "asset": "BTC",
        "market_price": "$67,890",
        "polymarket_implied": "$72,000",
        "divergence": "-5.7%",
        "opportunity": "Market pricing lower than prediction markets"
      }
    ]
  },

  "event_horizon": {
    "next_24h": [
      {
        "time": "2:00 PM ET",
        "event": "Fed Chair Speech",
        "impact": "High volatility expected in bonds and USD",
        "your_exposure": "Moderate (indirect via stocks)"
      }
    ],
    "earnings_this_week": [
      {"symbol": "AAPL", "date": "Thursday", "expected_move": "±3%"}
    ]
  },

  "strategy_reminder": {
    "your_words": "I'm bullish on tech but want to take profits when VIX spikes",
    "current_applicability": "VIX is low (16.5), no action needed on hedges"
  }
}
```

### Data Freshness Guarantees

| Data Type | Max Age | Update Mechanism |
|-----------|---------|------------------|
| Prices | 5 seconds | WebSocket feeds |
| Positions | 30 seconds | Broker API sync |
| Polymarket | 60 seconds | Polling with cache |
| News | 5 minutes | Streaming + digest |
| Events | 1 hour | Calendar API sync |
| Macro | 4 hours | Daily data sources |

### Token Budget Management

LLMs have context limits. We prioritize:

```
Priority 1 (Always included):
- Your portfolio summary: ~500 tokens
- Critical alerts (price moves, news): ~300 tokens

Priority 2 (Usually included):
- Held asset price action: ~400 tokens
- Relevant Polymarket signals: ~600 tokens

Priority 3 (If space allows):
- Market snapshot: ~300 tokens
- Event horizon: ~400 tokens

Priority 4 (Brief mentions):
- Macro context: ~200 tokens
- Strategy reminder: ~100 tokens

Total target: < 3000 tokens for fast/cheap models
Full context: < 8000 tokens for Claude/GPT-4
```

## Implementation Architecture

### Component Diagram

```python
# Core classes

class ContextOrchestrator:
    """Main entry point for context assembly."""

    def __init__(self):
        self.cache = TieredCache()  # Redis/memory
        self.collector = DataCollector()
        self.relevance = RelevanceEngine()
        self.builder = ContextBuilder()

    async def get_context_for(
        self,
        decision_type: str,
        symbols: List[str],
        user_strategy: str
    ) -> TradingContext:
        # Check cache for non-critical data
        cached = self.cache.get(decision_type)

        # Collect fresh data (parallel)
        raw = await self.collector.collect(symbols, decision_type)

        # Filter and prioritize
        filtered = self.relevance.filter(raw, decision_type)

        # Build LLM-optimized output
        context = self.builder.build(filtered, user_strategy)

        return context

class TieredCache:
    """
    Multi-level caching based on data volatility.

    L1: In-memory (prices, positions) - 1s TTL
    L2: Redis (sentiment, news) - 5min TTL
    L3: Disk (macro, events) - 1hr TTL
    """
```

### Data Flow for Trading Decision

```
User/Scheduler: "Check if we should trim AAPL position"

                    │
                    ▼
┌──────────────────────────────────────────┐
│  ContextOrchestrator.get_context_for()   │
│  (decision_type="position_review",       │
│   symbols=["AAPL"])                      │
└──────────────────┬───────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐     ┌───────────────┐
│  Data Sources │     │  Cache Check  │
│               │     │               │
│ • AAPL price  │     │ • Last known  │
│   (WebSocket) │     │   portfolio   │
│ • Related     │     │ • Recent news │
│   Polymarket  │     │   digest      │
│ • Apple news  │     └───────┬───────┘
│ • Market      │             │
│   context     │             ▼
└───────┬───────┘     ┌───────────────┐
        │             │  Cache hit?   │
        │             │  Yes → Return │
        │             │  No  → Fetch  │
        │             └───────┬───────┘
        │                     │
        └──────────┬──────────┘
                   ▼
        ┌───────────────────┐
        │  RelevanceEngine  │
        │                   │
        │ Filter: Only AAPL │
        │ news from last    │
        │ 6 hours           │
        │                   │
        │ Rank: Earnings    │
        │ news > General    │
        │ news              │
        └─────────┬─────────┘
                  ▼
        ┌───────────────────┐
        │  ContextBuilder   │
        │                   │
        │ Format for LLM:   │
        │ "AAPL position:   │
        │ +23.7% YTD..."    │
        └─────────┬─────────┘
                  ▼
        ┌───────────────────┐
        │  TradingContext   │
        │  (JSON structure) │
        └───────────────────┘
                  │
                  ▼
        Sent to LLM for decision
```

## Cost & Performance Optimization

### API Cost Management

| Data Source | Cost | Optimization |
|-------------|------|--------------|
| Alpaca | Free | Use WebSocket for streaming |
| OKX | Free | REST API only when needed |
| Polymarket | Free | 60-second polling |
| News API | $$$ | Cache aggressively, filter by relevance |
| LLM | $$$ | Summarize long content before sending |

### Latency Budget

| Operation | Target | Max |
|-----------|--------|-----|
| Price fetch | <100ms | 500ms |
| Full context assembly | <1s | 3s |
| LLM decision | <3s | 10s |
| Total decision cycle | <5s | 15s |

## Summary

This architecture ensures:

1. **Freshness**: Real-time prices, recent sentiment, latest news
2. **Relevance**: Only data affecting your positions and strategy
3. **Efficiency**: Aggressive caching, parallel fetching
4. **Clarity**: Structured for LLM understanding
5. **Cost control**: Tiered caching, API optimization

The LLM receives a curated briefing - like having a professional analyst prepare a summary rather than dumping raw data feeds.
