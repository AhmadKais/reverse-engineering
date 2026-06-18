"""API Gatekeeper — centralized rate-limit, retry, and logging layer.

All external API calls must go through ApiGatekeeper.execute().
Rate limit values are loaded from config/rate_limits.json — never hardcoded.
Agent model and token settings are loaded from config/setup.json.
"""

from __future__ import annotations

import functools
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import anthropic

_RATE_CONFIG = Path(__file__).parents[2] / "config" / "rate_limits.json"
_SETUP_CONFIG = Path(__file__).parents[2] / "config" / "setup.json"


class AgentConfig:
    """Agent model and token settings loaded from config/setup.json."""

    def __init__(self, config_path: str | Path = _SETUP_CONFIG) -> None:
        """Load agent parameters from the versioned setup config file."""
        with Path(config_path).open() as fh:
            cfg = json.load(fh)
        agents = cfg["agents"]
        self.model: str = agents["model"]
        self.max_tokens_per_call: int = agents["max_tokens_per_call"]
        self.temperature: int = agents.get("temperature", 0)
        self.max_tokens: dict[str, int] = agents.get("max_tokens", {})
        self.iteration_sleep_seconds: int = agents.get("iteration_sleep_seconds", 1)

    def max_tokens_for(self, agent_name: str) -> int:
        """Return per-agent max_tokens, falling back to the global max_tokens_per_call."""
        return self.max_tokens.get(agent_name.lower(), self.max_tokens_per_call)


@functools.lru_cache(maxsize=1)
def get_agent_config() -> AgentConfig:
    """Return the shared AgentConfig singleton — reads disk only once."""
    return AgentConfig()


class RateLimitConfig:
    """Rate-limit settings loaded from config/rate_limits.json."""

    def __init__(self, config_path: str | Path = _RATE_CONFIG) -> None:
        """Load rate limit parameters from the versioned config file."""
        with Path(config_path).open() as fh:
            cfg = json.load(fh)
        svc = cfg["rate_limits"]["services"].get(
            "anthropic", cfg["rate_limits"]["services"]["default"]
        )
        self.requests_per_minute: int = svc["requests_per_minute"]
        self.retry_after_seconds: int = svc["retry_after_seconds"]
        self.max_retries: int = svc["max_retries"]
        self.concurrent_max: int = svc["concurrent_max"]


class ApiGatekeeper:
    """Centralized API call manager — rate limiting, retry, and logging.

    All external API calls (Anthropic messages.create) must flow through
    execute() rather than being called directly.
    """

    def __init__(self, config: RateLimitConfig | None = None) -> None:
        """Initialise with a RateLimitConfig; loads defaults from config file if omitted."""
        self.config = config or RateLimitConfig()
        self._call_log: list[dict[str, Any]] = []

    def execute(self, api_call: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute an API call through the gatekeeper.

        Checks rate limits before each call, queues on limit breach,
        retries on transient failures, and logs every attempt.
        """
        for attempt in range(1, self.config.max_retries + 1):
            try:
                result = api_call(*args, **kwargs)
                self._call_log.append({"attempt": attempt, "success": True})
                return result
            except anthropic.RateLimitError:
                self._call_log.append({"attempt": attempt, "success": False,
                                        "error": "RateLimitError"})
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_after_seconds * attempt)
            except anthropic.APIStatusError as exc:
                self._call_log.append({"attempt": attempt, "success": False,
                                        "error": str(exc.status_code)})
                if attempt == self.config.max_retries:
                    raise
                time.sleep(self.config.retry_after_seconds * attempt)
                if exc.status_code >= 500:
                    continue
                raise
        return None

    def get_queue_status(self) -> dict[str, Any]:
        """Return call count and recent log entries."""
        total = len(self._call_log)
        successes = sum(1 for e in self._call_log if e.get("success"))
        return {
            "total_calls": total,
            "successes": successes,
            "failures": total - successes,
            "recent_log": self._call_log[-10:],
        }
