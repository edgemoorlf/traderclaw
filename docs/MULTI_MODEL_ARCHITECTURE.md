# TraderClaw Multi-Model Architecture

## Design Philosophy

**Separation of Concerns:**
- **Data Layer (Gemini)**: Fetches fresh market data, news, Polymarket via Google Search
- **Strategy Layer (Pluggable)**: DeepSeek (default), Claude, GPT, Qwen analyze and decide
- **Execution Layer**: Alpaca/OKX for order execution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-MODEL TRADING PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 1: DATA INTELLIGENCE (Gemini + Google Search)                 │   │
│   │                                                                     │   │
│   │  User: "Should I sell my AAPL position?"                            │   │
│   │                                                                     │   │
│   │  Gemini with Search Tools:                                          │   │
│   │  • Search "AAPL stock price today"                                  │   │
│   │  • Search "Apple news earnings March 2026"                          │   │
│   │  • Search "Polymarket Apple iPhone sales prediction"                │   │
│   │  • Search "Fed interest rate decision impact tech stocks"           │   │
│   │                                                                     │   │
│   │  Output: Structured Data Package                                    │   │
│   │  {                                                                  │   │
│   │    "aapl_price": 185.50,                                            │   │
│   │    "aapl_change_1d": "+2.3%",                                       │   │
│   │    "key_news": [...],                                               │   │
│   │    "polymarket_signals": [...],                                     │   │
│   │    "market_context": "Risk-on, tech rally"                          │   │
│   │  }                                                                  │   │
│   └──────────────────────────┬──────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 2: USER CONTEXT (Database/API)                                │   │
│   │                                                                     │   │
│   │  Fetch from local storage:                                          │   │
│   │  • User's AAPL position: 100 shares @ $150 avg                      │   │
│   │  • Portfolio allocation: 12% in AAPL                                │   │
│   │  • User's strategy: "Take profits at +20%"                          │   │
│   │  • Risk tolerance: Moderate                                         │   │
│   └──────────────────────────┬──────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 3: STRATEGY ANALYSIS (Pluggable LLM)                          │   │
│   │                                                                     │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │   │
│   │  │  DeepSeek   │  │    Qwen     │  │   Claude    │  │    GPT    │  │   │
│   │  │  (default)  │  │  (option)   │  │  (option)   │  │  (option) │  │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │   │
│   │                                                                     │   │
│   │  Input: Combined context (Gemini data + User positions)             │   │
│   │                                                                     │   │
│   │  Prompt: "You are a trading strategist. Given this market data     │   │
│   │  and the user's position, advise on the optimal action.            │   │
│   │  Consider: entry price, current P&L, market conditions,            │   │
│   │  upcoming catalysts, and the user's stated strategy."              │   │
│   │                                                                     │   │
│   │  Output: Trading Decision                                           │   │
│   │  {                                                                  │   │
│   │    "recommendation": "PARTIAL_SELL",                                │   │
│   │    "rationale": "Position up 23%, nearing target...",               │   │
│   │    "suggested_action": "Sell 50 shares",                            │   │
│   │    "confidence": "high",                                            │   │
│   │    "risks": ["Earnings next week"]                                  │   │
│   │  }                                                                  │   │
│   └──────────────────────────┬──────────────────────────────────────────┘   │
│                              │                                               │
│                              ▼                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 4: EXECUTION                                                  │   │
│   │                                                                     │   │
│   │  Based on operational mode:                                         │   │
│   │                                                                     │   │
│   │  • ADVISORY: Show recommendation to user                            │   │
│   │  • APPROVAL: Ask user to confirm                                    │   │
│   │  • AUTONOMOUS: Execute via Alpaca/OKX                               │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Why This Separation Works

| Layer | Model | Strength | Why Here |
|-------|-------|----------|----------|
| **Data** | Gemini | Google Search integration | Real-time web data, news, prices |
| **Strategy** | DeepSeek/Qwen/Claude | Reasoning, analysis | Trading logic, risk assessment |
| **Execution** | - | Broker APIs | Order placement, position tracking |

## Implementation

### 1. Gemini Data Agent

```python
# src/ai/gemini_data_agent.py

import google.generativeai as genai
from typing import Dict, List, Any


class GeminiDataAgent:
    """
    Fetches fresh market data using Gemini's Google Search capabilities.
    Output is structured data for the strategy model to consume.
    """

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Use Gemini Pro with search tool
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            tools=["google_search"]  # Enable search
        )

    async def gather_market_data(
        self,
        symbols: List[str],
        topics: List[str] = None
    ) -> Dict[str, Any]:
        """
        Use Gemini to search and compile market data.

        Args:
            symbols: Stock/crypto tickers (e.g., ["AAPL", "BTC"])
            topics: Additional topics to research

        Returns:
            Structured data package
        """

        # Build search prompt
        search_prompt = f"""Search for current market information about: {', '.join(symbols)}

Additional topics: {topics or 'general market sentiment'}

For each symbol, find:
1. Current price and daily change
2. Key news from today
3. Any upcoming events (earnings, Fed decisions)
4. Related prediction market sentiment if available

Output as structured JSON:
{{
  "market_summary": "brief overall conditions",
  "symbols": {{
    "SYMBOL": {{
      "price": current_price,
      "change_24h": "percentage",
      "change_1h": "percentage",
      "key_news": ["headline 1", "headline 2"],
      "upcoming_events": ["earnings on X date"],
      "sentiment": "bullish/neutral/bearish"
    }}
  }}
}}"""

        response = await self.model.generate_content_async(search_prompt)

        # Parse structured output
        return self._parse_gemini_output(response.text)

    async def search_polymarket_signals(self, events: List[str]) -> List[Dict]:
        """
        Search for prediction market data via Gemini.
        """
        prompt = f"""Search Polymarket and prediction markets for these events:
{chr(10).join(f"- {e}" for e in events)}

For each, find:
- Current odds/probability
- Trading volume
- Recent changes in sentiment
- Smart money indicators

Output structured data."""

        response = await self.model.generate_content_async(prompt)
        return self._parse_polymarket_data(response.text)

    async def get_macro_context(self) -> Dict[str, Any]:
        """
        Get broader market context (Fed, VIX, sectors).
        """
        prompt = """Search for current macro market conditions:
- Fed policy and rate expectations
- VIX level and trend
- Sector performance (tech, energy, finance)
- Major market-moving events today

Output as structured JSON."""

        response = await self.model.generate_content_async(prompt)
        return self._parse_macro_data(response.text)
```

### 2. Pluggable Strategy Agent

```python
# src/ai/strategy_agent.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class StrategyModel(Enum):
    """Supported strategy models."""
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    CLAUDE = "claude"
    GPT = "gpt"
    GEMINI = "gemini"


@dataclass
class TradingDecision:
    """Structured output from strategy model."""
    recommendation: str  # BUY, SELL, HOLD, PARTIAL_SELL, etc.
    symbol: str
    quantity: Optional[float]
    confidence: str  # high, medium, low
    rationale: str
    risks: list
    timeframe: str  # immediate, today, this_week


class StrategyAgent(ABC):
    """Abstract base for strategy models."""

    @abstractmethod
    async def analyze(
        self,
        market_data: Dict[str, Any],
        user_context: Dict[str, Any],
        query: str
    ) -> TradingDecision:
        """
        Analyze market data and make trading decision.

        Args:
            market_data: Output from GeminiDataAgent
            user_context: User's positions, strategy, preferences
            query: Original user question

        Returns:
            TradingDecision with recommendation
        """
        pass


class DeepSeekStrategyAgent(StrategyAgent):
    """DeepSeek for trading strategy (default)."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com"

    async def analyze(
        self,
        market_data: Dict[str, Any],
        user_context: Dict[str, Any],
        query: str
    ) -> TradingDecision:

        prompt = self._build_strategy_prompt(
            market_data, user_context, query
        )

        # Call DeepSeek API
        response = await self._call_deepseek(prompt)

        return self._parse_decision(response)

    def _build_strategy_prompt(
        self,
        market_data: Dict,
        user_context: Dict,
        query: str
    ) -> str:
        """Build prompt optimized for DeepSeek's reasoning."""

        return f"""You are an expert trading strategist analyzing market conditions.

## MARKET DATA (Fresh from today's markets)
```json
{self._format_json(market_data)}
```

## YOUR PORTFOLIO CONTEXT
```json
{self._format_json(user_context)}
```

## USER QUESTION
"{query}"

## YOUR TASK
Based on the market data and the user's position, provide a trading recommendation.

Think through this step by step:
1. What is the current market condition for this asset?
2. How does this position fit in the user's overall portfolio?
3. What are the key risks and catalysts?
4. What would be the optimal action and why?

Output your decision as JSON:
```json
{{
  "recommendation": "HOLD|BUY|SELL|PARTIAL_SELL",
  "symbol": "TICKER",
  "quantity": null or number,
  "confidence": "high|medium|low",
  "rationale": "Detailed explanation...",
  "risks": ["risk 1", "risk 2"],
  "timeframe": "immediate|today|this_week"
}}
```

Be decisive but acknowledge uncertainty. Consider both technical and fundamental factors."""


class ClaudeStrategyAgent(StrategyAgent):
    """Claude for conservative, safety-focused strategies."""

    def __init__(self, api_key: str):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)

    async def analyze(
        self,
        market_data: Dict[str, Any],
        user_context: Dict[str, Any],
        query: str
    ) -> TradingDecision:

        prompt = f"""You are a conservative trading advisor prioritizing capital preservation.

Market Data:
{market_data}

User Context:
{user_context}

Question: {query}

Provide a well-reasoned recommendation with explicit risk warnings."""

        response = await self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_decision(response.content[0].text)


class QwenStrategyAgent(StrategyAgent):
    """Alibaba Qwen for cost-effective analysis."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        # DashScope is Alibaba's API platform for Qwen
        self.base_url = "https://dashscope.aliyuncs.com"

    async def analyze(
        self,
        market_data: Dict[str, Any],
        user_context: Dict[str, Any],
        query: str
    ) -> TradingDecision:
        # Implementation for Qwen via DashScope
        pass


class StrategyAgentFactory:
    """Factory to create the appropriate strategy agent."""

    _agents = {
        StrategyModel.DEEPSEEK: DeepSeekStrategyAgent,
        StrategyModel.CLAUDE: ClaudeStrategyAgent,
        StrategyModel.QWEN: QwenStrategyAgent,
        # Add more as needed
    }

    @classmethod
    def create(
        cls,
        model: StrategyModel,
        api_key: str
    ) -> StrategyAgent:
        agent_class = cls._agents.get(model)
        if not agent_class:
            raise ValueError(f"Unknown strategy model: {model}")
        return agent_class(api_key)
```

### 3. Orchestrator

```python
# src/ai/orchestrator.py

from typing import Optional


class TradingOrchestrator:
    """
    Coordinates the multi-model pipeline:
    1. Gemini fetches data
    2. Strategy model analyzes
    3. User context applied
    4. Decision returned
    """

    def __init__(
        self,
        gemini_api_key: str,
        strategy_model: StrategyModel = StrategyModel.DEEPSEEK,
        strategy_api_key: str = None,
    ):
        self.data_agent = GeminiDataAgent(gemini_api_key)
        self.strategy_agent = StrategyAgentFactory.create(
            strategy_model, strategy_api_key
        )
        # For fetching user's actual positions
        self.position_service = PositionService()

    async def advise(
        self,
        user_id: str,
        query: str,
        symbols: Optional[list] = None
    ) -> TradingDecision:
        """
        Main entry point for trading advice.

        Pipeline:
        1. Parse query to identify relevant symbols
        2. Gemini fetches fresh market data
        3. Fetch user's positions and strategy
        4. Strategy model analyzes and decides
        5. Return structured recommendation
        """

        # Step 1: Identify symbols from query if not provided
        if not symbols:
            symbols = self._extract_symbols(query)

        # Step 2: Fetch fresh market data via Gemini
        print(f"🔍 Gathering market data for: {symbols}")
        market_data = await self.data_agent.gather_market_data(symbols)

        # Also get macro context
        macro_data = await self.data_agent.get_macro_context()
        market_data["macro"] = macro_data

        # Step 3: Fetch user context (positions, strategy)
        print(f"📊 Fetching portfolio context...")
        user_context = await self.position_service.get_user_context(user_id)

        # Step 4: Strategy model analyzes
        print(f"🧠 Analyzing with {self.strategy_agent.__class__.__name__}...")
        decision = await self.strategy_agent.analyze(
            market_data=market_data,
            user_context=user_context,
            query=query
        )

        # Step 5: Log for audit trail
        await self._log_decision(user_id, query, market_data, decision)

        return decision

    def _extract_symbols(self, query: str) -> list:
        """Extract stock/crypto symbols from natural language query."""
        # Could use Gemini or simple regex/NER
        # For now, simple approach
        import re
        # Match uppercase 1-5 letter words (stock tickers)
        tickers = re.findall(r'\b[A-Z]{1,5}\b', query)
        return list(set(tickers))  # Remove duplicates
```

### 4. Configuration

```yaml
# config/ai_models.yaml

models:
  # Data gathering (fixed - Gemini has best search)
  data_agent:
    provider: gemini
    model: gemini-1.5-pro
    api_key: ${GEMINI_API_KEY}
    tools:
      - google_search

  # Strategy agent (pluggable)
  strategy_agent:
    # Choose one: deepseek, qwen, claude, gpt
    provider: ${STRATEGY_MODEL_PROVIDER:-deepseek}

    deepseek:
      model: deepseek-chat
      api_key: ${DEEPSEEK_API_KEY}
      base_url: https://api.deepseek.com

    qwen:
      model: qwen-max
      api_key: ${DASHSCOPE_API_KEY}  # Alibaba's platform
      base_url: https://dashscope.aliyuncs.com

    claude:
      model: claude-3-opus-20240229
      api_key: ${ANTHROPIC_API_KEY}

    gpt:
      model: gpt-4-turbo
      api_key: ${OPENAI_API_KEY}
```

### 5. Usage Example

```python
# Initialize orchestrator
orchestrator = TradingOrchestrator(
    gemini_api_key=os.getenv("GEMINI_API_KEY"),
    strategy_model=StrategyModel.DEEPSEEK,  # or CLAUDE, QWEN, etc.
    strategy_api_key=os.getenv("DEEPSEEK_API_KEY")
)

# Get advice
decision = await orchestrator.advise(
    user_id="user_123",
    query="Should I sell my AAPL position? It's up 23%"
)

print(f"Recommendation: {decision.recommendation}")
print(f"Rationale: {decision.rationale}")
print(f"Confidence: {decision.confidence}")

# Output:
# Recommendation: PARTIAL_SELL
# Rationale: Position is up 23% exceeding your 20% target.
#   Earnings next week creates uncertainty. Consider taking
#   half profits and letting rest run with stop-loss.
# Confidence: high
```

## Model Selection Guide

| Use Case | Recommended Strategy Model | Why |
|----------|---------------------------|-----|
| **Default/General** | DeepSeek | Cost-effective, good reasoning, fast |
| **Conservative/Safety** | Claude | Best at risk assessment, cautious advice |
| **Complex Analysis** | GPT-4 | Strongest overall reasoning, worth the cost |
| **Cost-Sensitive** | Qwen | Very cheap via DashScope, decent quality |
| **Speed Critical** | DeepSeek | Fastest inference for real-time decisions |

## Cost Estimation (per query)

| Component | Model | Cost |
|-----------|-------|------|
| Data gathering | Gemini Pro + Search | ~$0.01-0.02 |
| Strategy (DeepSeek) | deepseek-chat | ~$0.002-0.005 |
| Strategy (Claude) | claude-3-opus | ~$0.03-0.06 |
| Strategy (GPT-4) | gpt-4-turbo | ~$0.02-0.04 |

**Typical query: $0.01-0.05 depending on strategy model**

## Next Steps

1. Implement `GeminiDataAgent` with search
2. Implement `DeepSeekStrategyAgent` (default)
3. Add factory for pluggable strategy models
4. Build orchestrator to wire it all together

**Should I implement these core classes?**