"""Strategy Agents - Pluggable LLM-based trading strategy analysis.

This module provides the "Strategy Layer" of the trading pipeline.
Multiple models are supported via a common interface.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
import anthropic

logger = logging.getLogger(__name__)


class StrategyModel(Enum):
    """Supported strategy model providers."""
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    CLAUDE = "claude"
    GPT = "gpt"
    GEMINI = "gemini"


@dataclass
class TradingDecision:
    """Structured output from strategy analysis."""
    recommendation: str  # BUY, SELL, HOLD, PARTIAL_SELL, PARTIAL_BUY, etc.
    symbol: str
    quantity: Optional[float]  # Number of shares/coins, or null for percentage-based
    quantity_type: str  # "shares", "percent_of_position", "percent_of_portfolio"
    confidence: str  # high, medium, low
    rationale: str  # Detailed explanation
    risks: List[str]  # Key risks identified
    timeframe: str  # immediate, today, this_week
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None


class StrategyAgent(ABC):
    """
    Abstract base class for strategy models.

    All strategy agents (DeepSeek, Claude, GPT, etc.) implement this interface
    for interchangeable use in the trading pipeline.
    """

    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model
        self.name = self.__class__.__name__

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
            market_data: Output from GeminiDataAgent (fresh market data)
            user_context: User's positions, strategy preferences, risk tolerance
            query: Original user question

        Returns:
            TradingDecision with structured recommendation
        """
        pass

    def _format_prompt(
        self,
        market_data: Dict[str, Any],
        user_context: Dict[str, Any],
        query: str
    ) -> str:
        """
        Format a standard strategy prompt.

        Can be overridden by subclasses for model-specific optimization.
        """
        return f"""You are an expert trading strategist providing actionable advice.

## MARKET DATA (Fresh)
```json
{json.dumps(market_data, indent=2, default=str)}
```

## YOUR PORTFOLIO CONTEXT
```json
{json.dumps(user_context, indent=2, default=str)}
```

## USER QUESTION
"{query}"

## YOUR TASK
Analyze the market data and portfolio context to provide a trading recommendation.

Think through:
1. What is the current market condition for the asset in question?
2. How does this position fit in the overall portfolio (concentration, correlation)?
3. What are the key risks and upcoming catalysts?
4. What would be the optimal action and position sizing?

Output your decision as JSON:
```json
{{
  "recommendation": "HOLD|BUY|SELL|PARTIAL_SELL|PARTIAL_BUY",
  "symbol": "TICKER",
  "quantity": null or number,
  "quantity_type": "shares|percent_of_position|percent_of_portfolio",
  "confidence": "high|medium|low",
  "rationale": "Detailed explanation with reasoning...",
  "risks": ["risk 1", "risk 2", "risk 3"],
  "timeframe": "immediate|today|this_week",
  "target_price": null or number,
  "stop_loss": null or number
}}
```

IMPORTANT:
- Be decisive but acknowledge uncertainty
- Consider both technical and fundamental factors
- Account for the user's stated strategy and risk tolerance
- Partial selling is often optimal for winning positions
- Always consider upcoming events (earnings, Fed, etc.)
- Respond in the same language as the user's question (e.g. if the question is in Chinese, write the rationale in Chinese)"""

    def _parse_decision(self, text: str, default_symbol: str = "") -> TradingDecision:
        """Parse structured JSON decision from model output."""
        try:
            # Extract JSON from response
            json_str = self._extract_json(text)
            data = json.loads(json_str)

            return TradingDecision(
                recommendation=data.get("recommendation", "HOLD").upper(),
                symbol=data.get("symbol", default_symbol).upper(),
                quantity=data.get("quantity"),
                quantity_type=data.get("quantity_type", "shares"),
                confidence=data.get("confidence", "medium").lower(),
                rationale=data.get("rationale", "No rationale provided"),
                risks=data.get("risks", []),
                timeframe=data.get("timeframe", "today").lower(),
                target_price=data.get("target_price"),
                stop_loss=data.get("stop_loss"),
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse decision: {e}")
            logger.debug(f"Raw text: {text}")
            # Return HOLD decision on parse error
            return TradingDecision(
                recommendation="HOLD",
                symbol=default_symbol,
                quantity=None,
                quantity_type="shares",
                confidence="low",
                rationale=f"Failed to parse model output: {e}",
                risks=["Parse error - manual review needed"],
                timeframe="immediate",
            )

    async def _call_llm(self, prompt: str) -> str:
        """Call the underlying LLM with a raw prompt and return the text response."""
        raise NotImplementedError

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that might contain markdown or extra content."""
        # Try to find JSON in code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end == -1:
                end = len(text)
            return text[start:end].strip()

        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end == -1:
                end = len(text)
            return text[start:end].strip()

        # Try to find JSON between curly braces
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]

        return text.strip()


class DeepSeekStrategyAgent(StrategyAgent):
    """
    DeepSeek strategy agent (default).

    Strengths:
    - Cost-effective
    - Good reasoning capabilities
    - Fast inference
    """

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        super().__init__(api_key, model)
        self.base_url = "https://api.deepseek.com"

    async def _call_llm(self, prompt: str) -> str:
        """Call DeepSeek with a raw prompt."""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert trading strategist. Always output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 2000,
            }
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"DeepSeek API error: {response.status} - {error_text}")
                result = await response.json()
                return result["choices"][0]["message"]["content"]

    async def analyze(
        self,
        market_data: Dict[str, Any],
        user_context: Dict[str, Any],
        query: str
    ) -> TradingDecision:
        """Analyze with DeepSeek."""
        logger.info("Analyzing with DeepSeek...")
        symbol = self._extract_symbol(query, user_context)
        try:
            content = await self._call_llm(self._format_prompt(market_data, user_context, query))
            return self._parse_decision(content, symbol)
        except Exception as e:
            logger.error(f"DeepSeek analysis failed: {e}")
            return TradingDecision(
                recommendation="HOLD", symbol=symbol, quantity=None,
                quantity_type="shares", confidence="low",
                rationale=f"Analysis failed: {e}",
                risks=["API error - manual review needed"], timeframe="immediate",
            )

    def _extract_symbol(self, query: str, context: Dict) -> str:
        """Extract symbol from query or context."""
        # Simple extraction - could be improved with NER
        import re
        tickers = re.findall(r'\b[A-Z]{1,5}\b', query)
        if tickers:
            return tickers[0]

        # Try to get from positions
        positions = context.get("positions", {})
        if positions:
            return list(positions.keys())[0]

        return "UNKNOWN"


class ClaudeStrategyAgent(StrategyAgent):
    """
    Claude strategy agent.

    Strengths:
    - Best at risk assessment and safety
    - Conservative, thoughtful recommendations
    - Excellent at explaining reasoning
    """

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        super().__init__(api_key, model)
        self.client = anthropic.Anthropic(api_key=api_key)

    async def analyze(
        self,
        market_data: Dict[str, Any],
        user_context: Dict[str, Any],
        query: str
    ) -> TradingDecision:
        """Analyze with Claude."""
        logger.info("Analyzing with Claude...")

        symbol = self._extract_symbol(query, user_context)

        # Claude-optimized prompt emphasizing safety
        prompt = f"""You are a conservative trading advisor prioritizing capital preservation.

Your approach:
1. Always identify risks first
2. Consider worst-case scenarios
3. Prefer gradual position changes over all-or-nothing
4. When uncertain, recommend holding

MARKET DATA:
{json.dumps(market_data, indent=2, default=str)}

PORTFOLIO CONTEXT:
{json.dumps(user_context, indent=2, default=str)}

USER QUESTION: "{query}"

Provide your recommendation as JSON:
{{
  "recommendation": "HOLD|BUY|SELL|PARTIAL_SELL|PARTIAL_BUY",
  "symbol": "TICKER",
  "quantity": number or null,
  "quantity_type": "shares|percent_of_position|percent_of_portfolio",
  "confidence": "high|medium|low",
  "rationale": "Explain your reasoning, focusing on risks...",
  "risks": ["primary risk", "secondary risk"],
  "timeframe": "immediate|today|this_week",
  "target_price": null or number,
  "stop_loss": null or number
}}

Respond in the same language as the user's question."""""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.content[0].text
            return self._parse_decision(content, symbol)
        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            return self._error_decision(symbol, str(e))

    async def _call_llm(self, prompt: str) -> str:
        """Call Claude with a raw prompt."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def _extract_symbol(self, query: str, context: Dict) -> str:
        """Extract symbol from query or context."""
        import re
        tickers = re.findall(r'\b[A-Z]{1,5}\b', query)
        if tickers:
            return tickers[0]

        positions = context.get("positions", {})
        if positions:
            return list(positions.keys())[0]

        return "UNKNOWN"

    def _error_decision(self, symbol: str, error: str) -> TradingDecision:
        """Create error decision."""
        return TradingDecision(
            recommendation="HOLD",
            symbol=symbol,
            quantity=None,
            quantity_type="shares",
            confidence="low",
            rationale=f"Claude analysis failed: {error}",
            risks=["API error - manual review needed"],
            timeframe="immediate",
        )


class QwenStrategyAgent(StrategyAgent):
    """
    Alibaba Qwen strategy agent via DashScope.

    Strengths:
    - Very cost-effective
    - Good Chinese market knowledge
    - Fast inference
    """

    def __init__(self, api_key: str, model: str = "qwen-max"):
        super().__init__(api_key, model)
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"

    async def analyze(
        self,
        market_data: Dict[str, Any],
        user_context: Dict[str, Any],
        query: str
    ) -> TradingDecision:
        """Analyze with Qwen via DashScope."""
        logger.info("Analyzing with Qwen...")
        symbol = self._extract_symbol(query, user_context)
        try:
            content = await self._call_llm(self._format_prompt(market_data, user_context, query))
            return self._parse_decision(content, symbol)
        except Exception as e:
            logger.error(f"Qwen analysis failed: {e}")
            return TradingDecision(
                recommendation="HOLD", symbol=symbol, quantity=None,
                quantity_type="shares", confidence="low",
                rationale=f"Qwen analysis failed: {e}",
                risks=["API error - manual review needed"], timeframe="immediate",
            )

    async def _call_llm(self, prompt: str) -> str:
        """Call Qwen with a raw prompt."""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "input": {
                    "messages": [
                        {"role": "system", "content": "You are a trading strategist. Output valid JSON only."},
                        {"role": "user", "content": prompt}
                    ]
                },
                "parameters": {"temperature": 0.2, "max_tokens": 2000},
            }
            async with session.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Qwen API error: {response.status} - {error_text}")
                result = await response.json()
                return result["output"]["text"]

    def _extract_symbol(self, query: str, context: Dict) -> str:
        """Extract symbol from query or context."""
        import re
        tickers = re.findall(r'\b[A-Z]{1,5}\b', query)
        if tickers:
            return tickers[0]

        positions = context.get("positions", {})
        if positions:
            return list(positions.keys())[0]

        return "UNKNOWN"


class StrategyAgentFactory:
    """Factory for creating strategy agents."""

    _agents = {
        StrategyModel.DEEPSEEK: DeepSeekStrategyAgent,
        StrategyModel.CLAUDE: ClaudeStrategyAgent,
        StrategyModel.QWEN: QwenStrategyAgent,
    }

    @classmethod
    def create(
        cls,
        model: StrategyModel,
        api_key: str,
        model_name: Optional[str] = None
    ) -> StrategyAgent:
        """
        Create a strategy agent.

        Args:
            model: The strategy model to use
            api_key: API key for the provider
            model_name: Specific model name (optional, uses default if not provided)

        Returns:
            StrategyAgent instance
        """
        agent_class = cls._agents.get(model)
        if not agent_class:
            raise ValueError(f"Unknown strategy model: {model}. "
                           f"Available: {list(cls._agents.keys())}")

        # Only pass model_name if provided, otherwise let agent use its default
        if model_name:
            return agent_class(api_key, model_name)
        return agent_class(api_key)

    @classmethod
    def create_from_string(
        cls,
        model_name: str,
        api_key: str
    ) -> StrategyAgent:
        """
        Create agent from string name.

        Args:
            model_name: String like "deepseek", "claude", "qwen"
            api_key: API key

        Returns:
            StrategyAgent instance
        """
        try:
            model = StrategyModel(model_name.lower())
            return cls.create(model, api_key)
        except ValueError:
            raise ValueError(f"Unknown model: {model_name}. "
                           f"Available: {[m.value for m in StrategyModel]}")

    @classmethod
    def list_available(cls) -> List[str]:
        """List available strategy models."""
        return [m.value for m in cls._agents.keys()]
