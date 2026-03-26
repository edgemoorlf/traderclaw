# TraderClaw Web UI Design (Position-Centric)

## Design Philosophy

**Start from where the user is - their existing portfolio.** The UI must:
1. **Import** user's current positions first
2. **Analyze** existing holdings and suggest strategies per position
3. **Create** strategies tied to specific positions (exit strategies, trim rules)
4. **Discover** new opportunities based on current exposure gaps

---

## Core User Flows

### Flow 1: Onboarding (Import Portfolio First)

```
┌─────────────────────────────────────────────────────────────────┐
│  WELCOME TO TRADERCLAW                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  To create personalized strategies, I need to see your          │
│  current portfolio first.                                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  📁 IMPORT YOUR PORTFOLIO                               │    │
│  │                                                         │    │
│  │  [Upload Fidelity CSV]  [Upload Schwab CSV]            │    │
│  │  [Connect Alpaca]  [Connect OKX]  [Enter Manually]     │    │
│  │                                                         │    │
│  │  Don't have a file? [Use Demo Portfolio]                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  YOUR PORTFOLIO IMPORTED                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📊 Total Value: $127,450    💰 Cash: $12,340                   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  YOUR POSITIONS                    P&L     Suggested    │    │
│  │  ─────────────────────────────────────────────────────  │    │
│  │  AAPL    150 shares   $28,450    +12.4%   [Strategy ▼] │    │
│  │  NVDA     80 shares   $42,180    +45.2%   [Strategy ▼] │    │
│  │  TSLA     60 shares   $18,920     -8.3%   [Strategy ▼] │    │
│  │  MSFT     45 shares   $25,610     +5.1%   [Strategy ▼] │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  [Next: Create Strategies for Your Positions →]                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Flow 2: Position-Centric Strategy Creation

Instead of creating abstract strategies, users create strategies FOR specific positions.

```
┌─────────────────────────────────────────────────────────────────┐
│  CREATE STRATEGY FOR: NVDA                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Your Position: 80 shares @ $527.25 avg  |  Current: +45.2%    │
│                                                                 │
│  What do you want to do with NVDA?                              │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  📈 TAKE        │  │  🛡️  PROTECT    │  │  ⏳ HOLD &      │  │
│  │  PROFITS        │  │  MY GAINS       │  │  ADD MORE       │  │
│  │                 │  │                 │  │                 │  │
│  │  "Sell when it  │  │  "Set a stop    │  │  "Buy the dip   │  │
│  │  hits my target │  │  loss to lock   │  │  if it drops    │  │
│  │  price"         │  │  in gains"      │  │  10%"           │  │
│  │                 │  │                 │  │                 │  │
│  │  [Select]       │  │  [Select]       │  │  [Select]       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  🚨 CUT LOSSES  │  │  💡 CUSTOM      │  │  🤖 AI          │  │
│  │  ON DROPS       │  │  STRATEGY       │  │  SUGGESTION     │  │
│  │                 │  │                 │  │                 │  │
│  │  "Sell if it    │  │  "I want to..." │  │  Based on your  │  │
│  │  drops below    │  │                 │  │  portfolio and  │  │
│  │  my cost basis" │  │  (Free text)    │  │  risk profile   │  │
│  │                 │  │                 │  │                 │  │
│  │  [Select]       │  │  [Select]       │  │  [See Ideas]    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Flow 3: Natural Language Strategy with Position Context

```
┌─────────────────────────────────────────────────────────────────┐
│  CUSTOM STRATEGY FOR NVDA                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Your Position Context:                                         │
│  • 80 shares @ $527.25 avg ($42,180 value)                     │
│  • Current price: $765.80 (+45.2% unrealized)                  │
│  • This is 33% of your portfolio (concentration risk!)         │
│                                                                 │
│  Describe what you want to do:                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ "Sell 50% when it hits $800, then set trailing stop    │    │
│  │  for the rest at 10% below peak"                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  💡 Suggestions based on your position:                         │
│  • "Trim 30% to reduce concentration risk"                     │
│  • "Take half profits at +50%, let rest run"                   │
│  • "Set stop loss at -20% from here to protect gains"          │
│                                                                 │
│  [Preview How This Will Work →]                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI INTERPRETATION & CONFIRMATION                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🤖 Here's how I understand your NVDA strategy:                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  STRATEGY: "Graduated Profit Taking with Trailing Stop" │    │
│  │                                                         │    │
│  │  YOUR POSITION: 80 shares @ $527.25 avg                │    │
│  │                                                         │    │
│  │  WHEN price reaches $800 (+4.5% from current):          │    │
│  │    → SELL 40 shares (50% of position)                  │    │
│  │    → Estimated proceeds: $32,000                       │    │
│  │    → Realized gain: ~$10,910 (+51% on sold shares)     │    │
│  │    → Remaining: 40 shares                              │    │
│  │                                                         │    │
│  │  THEN for remaining 40 shares:                          │    │
│  │    → Set trailing stop at 10% below highest price      │    │
│  │    → Currently: triggers if price drops below $689     │    │
│  │    → This protects ~$6,470 of remaining gains          │    │
│  │                                                         │    │
│  │  PORTFOLIO IMPACT AFTER FIRST SELL:                     │    │
│  │    • NVDA allocation: 33% → 16%                        │    │
│  │    • Cash position: $12,340 → $44,340                  │    │
│  │    • Realized gains this year: +$10,910                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ⚠️  Need clarification:                                        │
│     "10% below peak" - Did you mean:                           │
│     (●) 10% below the $800 sell point (fixed at $720)          │
│     ( ) 10% below whatever the highest price reaches (trailing)│
│                                                                 │
│  [Edit Description]  [✓ This is exactly what I want]            │
└─────────────────────────────────────────────────────────────────┘
```

### Flow 4: Multi-Position Strategy (Portfolio-Level Rules)

```
┌─────────────────────────────────────────────────────────────────┐
│  CREATE PORTFOLIO-WIDE STRATEGY                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  This strategy will apply to ALL your positions.                │
│                                                                 │
│  What should I watch across your portfolio?                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  "If any position gains more than 50%, sell half to    │    │
│  │   lock in profits"                                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  🤖 This will apply to:                                         │
│  • NVDA: Currently +45.2% (will trigger at +50%)               │
│  • AAPL: Currently +12.4%                                       │
│  • MSFT: Currently +5.1%                                        │
│  • TSLA: Currently -8.3% (won't trigger yet)                   │
│                                                                 │
│  PREVIEW OF WHAT WOULD HAPPEN:                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  NVDA at +50% gain ($790.87):                           │    │
│  │    → Sell 40 shares (half of 80)                       │    │
│  │    → Realize ~$10,545 profit                           │    │
│  │    → Keep 40 shares for further upside                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  [Apply to All Positions]  [Select Specific Positions →]        │
└─────────────────────────────────────────────────────────────────┘
```

### Flow 5: Main Dashboard (Position + Strategy View)

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 TRADERCLAW DASHBOARD                           [⚙️] [👤]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Portfolio: $127,450    Today: +$1,240 (+0.98%)    🟢 Running   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  YOUR POSITIONS                    Strategy     Status  │    │
│  │  ─────────────────────────────────────────────────────  │    │
│  │  🟢 AAPL  $28,450  +12.4%         "Hold until   Active  │    │
│  │     150 sh @ $189.67              $220 or -10%"        │    │
│  │                                                         │    │
│  │  🟢 NVDA  $42,180  +45.2%         "Sell 50% @   Active  │    │
│  │      80 sh @ $527.25              $800, trail"         │    │
│  │                                                         │    │
│  │  ⚠️  TSLA  $18,920  -8.3%         "Cut losses    Pending│    │
│  │      60 sh @ $315.33              at -15%"    Approval │    │
│  │                                                         │    │
│  │  🟢 MSFT  $25,610  +5.1%          [+ Add Strategy]      │    │
│  │      45 sh @ $569.11                                    │    │
│  │                                                         │    │
│  │  💵 CASH  $12,340                                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  🔔 ACTIVE ALERTS                                       │    │
│  │                                                         │    │
│  │  NVDA approaching first target!                         │    │
│  │  Current: $765  |  Target: $800  |  4.6% to go          │    │
│  │  [View Details]  [Modify Target]                        │    │
│  │                                                         │    │
│  │  TSLA approaching your stop loss zone                   │    │
│  │  Current: $315  |  Your stop: -15% from $315 = $268    │    │
│  │  Currently 12% above your stop level                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  [+ New Strategy]  [⚡ Quick Trade]  [📈 Discover Ideas]        │
└─────────────────────────────────────────────────────────────────┘
```

### Flow 6: Signal Approval (Position-Aware)

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️  STRATEGY SIGNAL: SELL NVDA                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Your strategy "Graduated Profit Taking" has triggered:        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    SELL SIGNAL                          │    │
│  │                                                         │    │
│  │  NVDA hit your target price of $800!                    │    │
│  │  Current: $805.50                                       │    │
│  │                                                         │    │
│  │  YOUR POSITION BEFORE:                                  │    │
│  │    • 80 shares @ $527.25 avg = $42,180                 │    │
│  │    • Unrealized gain: +$22,260 (+52.8%)                │    │
│  │                                                         │    │
│  │  PROPOSED ACTION:                                       │    │
│  │    → SELL 40 shares (50%) @ ~$805                      │    │
│  │    → Realized gain: $11,130                            │    │
│  │    → Proceeds: $32,200 (minus taxes)                   │    │
│  │                                                         │    │
│  │  YOUR POSITION AFTER:                                   │    │
│  │    • 40 shares remaining (~$32,220 value)              │    │
│  │    • Trailing stop set at 10% below $805 = $724.50     │    │
│  │    • If triggered: protects ~$7,890 of gains           │    │
│  │                                                         │    │
│  │  PORTFOLIO IMPACT:                                      │    │
│  │    • NVDA concentration: 33% → 16%                     │    │
│  │    • Cash available: $12,340 → $44,540                 │    │
│  │    • Tax estimate (short-term): ~$3,340                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  [✓ Execute 40 Shares]  [Sell Different Amount]  [✗ Skip]      │
│  [Pause This Strategy]                                          │
│                                                                 │
│  ⏱️ Auto-execute in 5:00 (high confidence: 94%)                 │
└─────────────────────────────────────────────────────────────────┘
```

### Flow 7: Quick Trade (With Position Context)

```
┌─────────────────────────────────────────────────────────────────┐
│  QUICK TRADE                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  You have:                                                      │
│  • AAPL: 150 shares (+12.4%)                                   │
│  • NVDA: 80 shares (+45.2%)   ← Selected                       │
│  • TSLA: 60 shares (-8.3%)                                     │
│  • MSFT: 45 shares (+5.1%)                                     │
│                                                                 │
│  NVDA: 80 shares @ $765.80  |  Total value: $61,264            │
│                                                                 │
│  I want to:  [Buy More ▼]  [Sell ▼]  [Set Alert ▼]             │
│                                                                 │
│  Sell:  [●] 40 shares (half)                                    │
│         [ ] 80 shares (all)                                     │
│         [ ] $20,000 worth                                       │
│         [ ] Custom: [____] shares                               │
│                                                                 │
│  Why are you selling? (helps me learn your style)               │
│  [●] Taking profits    [ ] Cutting losses    [ ] Rebalancing   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  ORDER PREVIEW:                                         │    │
│  │  Sell 40 NVDA @ market (~$765.80) = $30,632            │    │
│  │  Estimated gain: +$9,542 (realized)                    │    │
│  │  Remaining position: 40 shares (~$30,632)              │    │
│  │                                                         │    │
│  │  💡 This matches your strategy: "Sell 50% @ $800"      │    │
│  │    Would you like to update your strategy target?      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  [Place Sell Order]  [Update Strategy Instead]                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key UI Components

### 1. Position Card with Strategy Status

```
┌─────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  AAPL                                   [Edit ▼]       │    │
│  │  Apple Inc.                                            │    │
│  │                                                         │    │
│  │  150 shares × $192.50 = $28,875        Today: +2.3%    │    │
│  │  Avg cost: $189.67    Unrealized: +$425 (+1.5%)        │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │  ACTIVE STRATEGY: "Hold until $220"            │    │    │
│  │  │                                                 │    │    │
│  │  │  Target: $220 (14% above current)              │    │    │
│  │  │  Stop loss: $170 (12% below current)           │    │    │
│  │  │                                                 │    │    │
│  │  │  [Modify]  [Pause]  [Replace]                  │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  │                                                         │    │
│  │  [+ Add Exit Strategy]  [View Chart]  [News]            │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Strategy Suggestion Engine

```
┌─────────────────────────────────────────────────────────────────┐
│  💡 SUGGESTED STRATEGIES FOR NVDA                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Based on your position (+45.2% gain, 33% of portfolio):       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  🎯 TAKE SOME PROFITS                                   │    │
│  │  You're up 45% - consider locking in gains              │    │
│  │  [Sell 50% now]  [Set target at $850]  [Set trailing]   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  ⚠️  RISK ALERT                                         │    │
│  │  NVDA is 33% of your portfolio (high concentration)     │    │
│  │  [Create diversification rule]                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  📈 LET WINNERS RUN                                     │    │
│  │  Keep position but protect with trailing stop           │    │
│  │  [Set 15% trailing stop]                                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  [Tell me more about these options]                             │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Ambiguity Resolution (Position Context)

```
┌─────────────────────────────────────────────────────────────────┐
│  🤔 Clarification Needed for TSLA Strategy                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Your position: 60 shares @ $315.33  |  Current: -8.3%         │
│                                                                 │
│  You said: "Sell if it keeps dropping"                          │
│                                                                 │
│  I can interpret this as:                                       │
│                                                                 │
│  (●) Sell if TSLA drops another 5% to $289 (total -13.3%)      │
│  ( ) Sell if TSLA hits your cost basis at $315 (breakeven)     │
│  ( ) Sell if TSLA drops 10% from here to $268 (total -18.3%)   │
│  ( ) Sell at market open tomorrow if it's still down           │
│                                                                 │
│  [Explain these options]  [✓ Use Selected Option]               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Backend Logic: Position-Aware Strategy Parsing

```python
class PositionAwareStrategyParser:

    def parse_strategy_for_position(
        self,
        user_input: str,
        position: Position
    ) -> ParsedStrategy:
        """
        Parse strategy with full context of user's existing position.
        """
        context = {
            "symbol": position.symbol,
            "shares": position.quantity,
            "avg_cost": position.avg_entry_price,
            "current_price": position.current_price,
            "unrealized_pnl_pct": position.unrealized_pnl_pct,
            "portfolio_weight": position.value / portfolio.total_value,
            "is_winner": position.unrealized_pnl_pct > 0.20,
            "is_loser": position.unrealized_pnl_pct < -0.10,
            "is_concentrated": position.value / portfolio.total_value > 0.25,
        }

        prompt = f"""
        The user owns {context['shares']} shares of {context['symbol']}
        at an average cost of ${context['avg_cost']:.2f}.
        Current price is ${context['current_price']:.2f}.
        They want to create a strategy: "{user_input}"

        Parse this into specific actions considering their position:
        - If selling: calculate exact shares to sell
        - If setting stops: calculate price levels
        - If adding: check cash available and concentration

        Return structured strategy with exact quantities and prices.
        Flag any ambiguities for clarification.
        """

        return self.llm.parse(prompt, context)

    def generate_position_aware_summary(
        self,
        strategy: ParsedStrategy,
        position: Position
    ) -> StrategySummary:
        """Generate summary showing exact impact on user's position."""

        # Calculate specific outcomes
        if strategy.action == "SELL_PARTIAL":
            shares_to_sell = int(position.quantity * strategy.percentage)
            proceeds = shares_to_sell * position.current_price
            realized_gain = shares_to_sell * (position.current_price - position.avg_cost)
            remaining_shares = position.quantity - shares_to_sell

            return {
                "title": f"Sell {strategy.percentage*100:.0f}% of {position.symbol}",
                "impact": {
                    "shares_sold": shares_to_sell,
                    "proceeds": proceeds,
                    "realized_gain": realized_gain,
                    "tax_estimate": realized_gain * 0.25,  # Short-term
                    "remaining_shares": remaining_shares,
                    "remaining_value": remaining_shares * position.current_price,
                },
                "portfolio_impact": {
                    "concentration_before": position.value / portfolio.total_value,
                    "concentration_after": (remaining_shares * position.current_price) / (portfolio.total_value + proceeds),
                    "cash_increase": proceeds,
                }
            }
```

---

## API Endpoints (Position-Centric)

```python
@app.get("/api/portfolio")
async def get_portfolio():
    """Get user's complete portfolio with positions and strategies."""
    return {
        "total_value": 127450.00,
        "cash": 12340.00,
        "positions": [
            {
                "symbol": "NVDA",
                "quantity": 80,
                "avg_cost": 527.25,
                "current_price": 765.80,
                "unrealized_pnl_pct": 0.452,
                "portfolio_weight": 0.33,
                "strategy": {...},  # Active strategy if any
            }
        ]
    }

@app.post("/api/positions/{symbol}/strategy")
async def create_position_strategy(
    symbol: str,
    input: StrategyInput,
    clarification_responses: dict = None
):
    """
    Create a strategy specifically for an existing position.
    Returns interpretation for user confirmation.
    """
    position = portfolio.get_position(symbol)
    parsed = parser.parse_strategy_for_position(input.description, position)

    if parsed.ambiguities and not clarification_responses:
        return {
            "status": "needs_clarification",
            "ambiguities": parsed.ambiguities,
            "preview": None
        }

    # Apply clarifications and generate final summary
    clarified = parser.apply_clarifications(parsed, clarification_responses)
    summary = parser.generate_position_aware_summary(clarified, position)

    return {
        "status": "ready_for_confirmation",
        "summary": summary,
        "requires_confirmation": True
    }

@app.post("/api/positions/{symbol}/strategy/confirm")
async def confirm_position_strategy(
    symbol: str,
    strategy_data: dict,
    confirmed: bool
):
    """Save strategy after user confirmation."""
    if not confirmed:
        raise HTTPException(400, "Strategy not confirmed")

    strategy = Strategy.create_for_position(symbol, strategy_data)
    return {"status": "created", "strategy_id": strategy.id}

@app.get("/api/positions/{symbol}/suggestions")
async def get_strategy_suggestions(symbol: str):
    """Get AI-generated strategy suggestions based on position context."""
    position = portfolio.get_position(symbol)
    return suggester.generate_suggestions(position)

@app.get("/api/signals/pending")
async def get_pending_signals():
    """Get all signals requiring user approval."""
    return {
        "signals": [
            {
                "id": "sig_123",
                "symbol": "NVDA",
                "action": "SELL",
                "quantity": 40,
                "reason": "Target price $800 reached",
                "position_context": {...},
                "portfolio_impact": {...},
            }
        ]
    }
```

---

## Key Differences from Original Design

| Aspect | Old Design | New Position-Centric Design |
|--------|-----------|----------------------------|
| **Starting Point** | Abstract strategy creation | Import portfolio first |
| **Strategy Context** | Symbols selected from scratch | Strategies tied to existing positions |
| **Action Types** | Entry-focused (BUY) | Exit-focused (SELL, TRIM, STOP) |
| **Impact Preview** | Generic position sizing | Exact shares, exact P&L impact |
| **Ambiguity** | Generic terms | Position-specific clarifications |
| **Suggestions** | Template-based | Based on position state (winner/loser/concentrated) |
| **Dashboard** | Strategy list | Position list with strategy status |

---

## Single-Screen Dashboard Design

Everything visible at once - no navigation required.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  📊 TRADERCLAW                              Portfolio: $127,450    Today: +$1,240 (+0.98%) │
│  ─────────────────────────────────────────────────────────────────────────────────────────  │
│                                                                                             │
│  ┌───────────────────────────────────────┐  ┌─────────────────────────────────────────┐    │
│  │  YOUR POSITIONS          P&L  Strategy│  │  🤖 AI ASSISTANT                        │    │
│  │  ─────────────────────────────────────│  │                                         │    │
│  │                                       │  │  What would you like to do?             │    │
│  │  🟢 NVDA  80sh  $765   +45% ⭐         │  │                                         │    │
│  │     $61,264  |  $527 cost             │  │  [📈 Take profits on NVDA]              │    │
│  │     "Sell 50% at $800" ✓ Active       │  │  [🛡️ Protect my TSLA position]          │    │
│  │                                       │  │  [💰 Invest idle cash]                  │    │
│  │  🟢 AAPL 150sh  $192   +12%           │  │  [📋 Create portfolio-wide rule]        │    │
│  │     $28,875  |  $190 cost             │  │                                         │    │
│  │     "Hold to $220" ✓ Active           │  │  ─────────────────────────────────────  │    │
│  │                                       │  │  Or type naturally:                     │    │
│  │  ⚠️  TSLA  60sh  $315   -8%  ⏸️        │  │  ┌─────────────────────────────────┐    │    │
│  │     $18,920  |  $315 cost             │  │  │ "Sell NVDA if it drops 10%"    │    │    │
│  │     "Stop at -15%" Pending approval   │  │  └─────────────────────────────────┘    │    │
│  │                                       │  │           [Ask AI]                      │    │
│  │  🟢 MSFT  45sh  $569   +5%            │  │                                         │    │
│  │     $25,610  |  No strategy           │  │                                         │    │
│  │     [+ Add Strategy]                  │  │                                         │    │
│  │                                       │  │                                         │    │
│  │  💵 CASH  $12,340                     │  │                                         │    │
│  │                                       │  │                                         │    │
│  └───────────────────────────────────────┘  └─────────────────────────────────────────┘    │
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │  🔔 ALERTS & SIGNALS                                                                │   │
│  │  ─────────────────────────────────────────────────────────────────────────────────  │   │
│  │                                                                                     │   │
│  │  🎯 NVDA approaching target!  $765 → $800 (94% there)                    [Modify]  │   │
│  │     Your "Sell 50% at $800" strategy will trigger soon                            │   │
│  │                                                                                     │   │
│  │  ⚡ New signal requires approval:                                                   │   │
│  │     SELL 40 NVDA @ ~$805 = $32,200 proceeds (+$11,130 gain)              [✓] [✗]   │   │
│  │     Remaining: 40 shares | Concentration: 33% → 16%                               │   │
│  │                                                                                     │   │
│  │  📊 TSLA 12% above your stop level ($315 → $268 stop)                             │   │
│  │                                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│  [⚙️ Settings]  [📤 Import/Export]  [📈 Charts]  [📝 Logs]        🟢 System Active         │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Single-Screen Layout Breakdown

| Section | Width | Content |
|---------|-------|---------|
| **Header** | Full | Total portfolio value, daily change, system status |
| **Positions (Left)** | 45% | All positions with mini-charts, P&L, strategy status |
| **AI Chat (Right)** | 55% | Quick action buttons + natural language input |
| **Alerts (Bottom)** | Full | Pending signals, approaching targets, status updates |
| **Footer** | Full | Quick links + system status |

### Expanding Panels (In-Place, No Navigation)

```
User clicks on NVDA position:
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  ... (rest of dashboard unchanged) ...                                                      │
│  ┌───────────────────────────────────────┐                                                  │
│  │  🟢 NVDA  80sh  $765   +45% ⭐  ▼     │  ◄── Expanded in-place                          │
│  │  ─────────────────────────────────────│                                                  │
│  │  Value: $61,264  |  Cost: $42,180     │                                                  │
│  │  Gain: +$19,084 (+45.2%) unrealized   │                                                  │
│  │  33% of portfolio ⚠️ Concentrated     │                                                  │
│  │                                       │                                                  │
│  │  [5d chart sparkline]                 │                                                  │
│  │                                       │                                                  │
│  │  ACTIVE STRATEGY:                     │                                                  │
│  │  "Sell 50% at $800, trail rest 10%"   │                                                  │
│  │  Status: 🟡 Approaching target (94%)  │                                                  │
│  │  [Edit] [Pause] [Replace] [Test]      │                                                  │
│  │                                       │                                                  │
│  │  SUGGESTED ADJUSTMENTS:               │                                                  │
│  │  • You're 33% concentrated → [Trim now]                                                 │
│  │  • Price near target → [Adjust to $850]                                                 │
│  │                                       │                                                  │
│  │  QUICK ACTIONS:                       │                                                  │
│  │  [Sell 25%] [Sell 50%] [Sell All] [Set Alert]                                           │
│  │                                       │                                                  │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│  ... (rest of dashboard still visible) ...                                                  │
```

### Inline Strategy Creation (No Modal)

```
User clicks [+ Add Strategy] on MSFT:
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  ...                                                                                        │
│  ┌───────────────────────────────────────┐  ┌─────────────────────────────────────────┐    │
│  │  🟢 MSFT  45sh  $569   +5%            │  │  AI is creating a strategy for MSFT...  │    │
│  │     $25,610  |  $569 cost             │  │                                         │    │
│  │  ─────────────────────────────────────│  │  What do you want to do with MSFT?      │    │
│  │                                       │  │                                         │    │
│  │  QUICK TEMPLATES:                     │  │  ┌─────────────────────────────────┐    │    │
│  │  [Take profits at +20%]               │  │  │ "Hold until $650 or cut at     │    │    │
│  │  [Protect with trailing stop]         │  │  │  -10%"                          │    │    │
│  │  [Add on dips]                        │  │  └─────────────────────────────────┘    │    │
│  │                                       │  │  [Quick Apply]  [Customize]             │    │
│  │  OR TYPE NATURALLY:                   │  │                                         │    │
│  │  ┌─────────────────────────────────┐  │  │  ───── Preview ─────                    │    │
│  │  │ "Sell if it drops below $500"  │  │  │  Entry: $569  |  Exit: $650 or $512     │    │
│  │  └─────────────────────────────────┘  │  │  Risk/Reward: 1:2.5                     │    │
│  │  [Analyze]                            │  │                                         │    │
│  │                                       │  │  [✓ Save Strategy]  [✗ Cancel]          │    │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
```

### Inline Signal Approval

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  ...                                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │  🔔 ALERTS & SIGNALS                                                                │   │
│  │                                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐   │   │
│  │  │  ⚡ ACTION REQUIRED: NVDA Target Reached!                                    │   │   │
│  │  │                                                                             │   │   │
│  │  │  Your position: 80 shares @ $527 avg  |  Current: $805 (+52.7%)            │   │   │
│  │  │  Strategy: "Sell 50% at $800"  →  TRIGGERED                                 │   │   │
│  │  │                                                                             │   │   │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │   │   │
│  │  │  │  EXECUTE        │  │  MODIFY         │  │  SKIP THIS      │             │   │   │
│  │  │  │                 │  │                 │  │                 │             │   │   │
│  │  │  │  Sell 40 shares │  │ Sell different  │  │ Keep all 80     │             │   │   │
│  │  │  │  @ ~$805        │  │ amount          │  │ shares          │             │   │   │
│  │  │  │                 │  │                 │  │                 │             │   │   │
│  │  │  │  = $32,200      │  │                 │  │ (update target) │             │   │   │
│  │  │  │  +$11,130 gain  │  │                 │  │                 │             │   │   │
│  │  │  └─────────────────┘  └─────────────────┘  └─────────────────┘             │   │   │
│  │  │                                                                             │   │   │
│  │  │  Impact: Cash $12,340 → $44,540 | NVDA 33% → 16% | Tax est: ~$2,800       │   │   │
│  │  │                                                                             │   │   │
│  │  │  ⏱️ Auto-execute in 4:59  |  Confidence: 94%                                │   │   │
│  │  └─────────────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│  ...                                                                                        │
```

---

## Implementation Plan
