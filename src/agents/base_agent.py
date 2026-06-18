"""Base agent — shared LLM call logic using the Anthropic SDK.

All three specialized agents (Navigator, Analyzer, Fixer) extend this class.
Every API call is routed through ApiGatekeeper — never called directly.
"""

from __future__ import annotations

import os

import anthropic
from dotenv import load_dotenv

from src.agents.gatekeeper import ApiGatekeeper, RateLimitConfig

load_dotenv()

_DEFAULT_MODEL = "claude-sonnet-4-6"
_DEFAULT_MAX_TOKENS = 1024


class TokenBudgetExceededError(Exception):
    """Raised when the shared token budget is exhausted."""


class AgentBudget:
    """Shared token budget across all agents — prevents runaway API costs."""

    def __init__(self, max_tokens: int = 50_000) -> None:
        """Initialise with a maximum token ceiling shared across all agents."""
        self.max_tokens = max_tokens
        self.used_input = 0
        self.used_output = 0

    @property
    def total_used(self) -> int:
        """Sum of input and output tokens consumed so far."""
        return self.used_input + self.used_output

    @property
    def remaining(self) -> int:
        """Tokens still available before the budget ceiling is hit."""
        return self.max_tokens - self.total_used

    def record(self, input_tokens: int, output_tokens: int) -> None:
        """Accumulate token usage; raise TokenBudgetExceededError if ceiling passed."""
        self.used_input += input_tokens
        self.used_output += output_tokens
        if self.total_used > self.max_tokens:
            raise TokenBudgetExceededError(
                f"Token budget exceeded: {self.total_used:,}/{self.max_tokens:,}"
            )

    def status(self) -> dict:
        """Return a snapshot dict of token usage and remaining budget."""
        return {
            "used_input": self.used_input,
            "used_output": self.used_output,
            "total_used": self.total_used,
            "remaining": self.remaining,
            "budget": self.max_tokens,
        }


class BaseAgent:
    """LLM-backed agent with budget enforcement and retry logic.

    Subclasses set their own system_prompt and call generate_response().
    Every API call goes through _call_llm() — never call anthropic directly.
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        budget: AgentBudget,
        model: str = _DEFAULT_MODEL,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        gatekeeper: ApiGatekeeper | None = None,
    ) -> None:
        """Wire up name, system prompt, budget, model, Anthropic client, and gatekeeper."""
        self.name = name
        self.system_prompt = system_prompt
        self.budget = budget
        self.model = model
        self.max_tokens = max_tokens
        self._client = anthropic.Anthropic(api_key=self._load_api_key())
        self._gatekeeper = gatekeeper or ApiGatekeeper(RateLimitConfig())
        self.history: list[dict] = []

    @staticmethod
    def _load_api_key() -> str:
        """Read ANTHROPIC_API_KEY from environment; raise OSError if absent."""
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise OSError("ANTHROPIC_API_KEY not set in environment or .env file")
        return key

    def _call_llm(self, messages: list[dict]) -> str:
        """Route one request through ApiGatekeeper with budget accounting."""
        response = self._gatekeeper.execute(
            self._client.messages.create,
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=messages,
        )
        if response is None:
            return ""
        self.budget.record(response.usage.input_tokens, response.usage.output_tokens)
        return self._extract_text(response)

    @staticmethod
    def _extract_text(response: anthropic.types.Message) -> str:
        """Extract the first text block from an Anthropic message response."""
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""

    def generate_response(self, user_message: str) -> str:
        """Append user message to history, call LLM, append assistant reply."""
        self.history.append({"role": "user", "content": user_message})
        reply = self._call_llm(self.history)
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def reset_history(self) -> None:
        """Clear conversation history to start a fresh multi-turn exchange."""
        self.history.clear()
