"""FIXED: base_agent.py — Bug #2 patch applied (SPOF: generate_response + hardcoded dispatch).

Changes from original:
  1. generate_response: wrapped in try/except with graceful fallback on WatchdogTimeoutError
     → removes SPOF: a timeout no longer crashes the agent silently
  2. _handle_tool_use: replaced hardcoded 'if block.name == "web_search"' with a
     pluggable tool registry (dict mapping name → handler callable)
     → removes HardcodedDispatch: new tools can be registered without touching BaseAgent
"""

import json

import anthropic

from src.core.config import get_api_key, load_config
from src.core.gatekeeper import Gatekeeper
from src.core.logger import FIFOLogger
from src.core.watchdog import Watchdog, WatchdogTimeoutError

# Type alias for a tool handler: receives tool input dict, returns str result
ToolHandler = callable


_FALLBACK_RESPONSE = "[Agent temporarily unavailable — timeout after all retries]"


class BaseAgent:
    """Common LLM call logic, tool execution, token tracking, and watchdog wrapping.

    FIX #1 (SPOF): generate_response now catches WatchdogTimeoutError and returns a
    safe fallback string instead of propagating the exception to the debate orchestrator.

    FIX #2 (HardcodedDispatch): tool handlers are registered in a dict (_tool_handlers)
    instead of being hardcoded as if-blocks inside _handle_tool_use.
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        gatekeeper: Gatekeeper,
        watchdog: Watchdog,
        logger: FIFOLogger,
        tools: list[dict] | None = None,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.gatekeeper = gatekeeper
        self.watchdog = watchdog
        self.logger = logger
        self.tools = tools or []
        cfg = load_config()
        self.model = cfg["model"]
        self._max_tool_rounds: int = cfg.get("max_tool_rounds", 5)
        self.max_tokens: int = 500
        self._client = anthropic.Anthropic(api_key=get_api_key())
        self.history: list[dict] = []

        # FIX #2: pluggable tool registry — register handlers here, not in _handle_tool_use
        self._tool_handlers: dict[str, ToolHandler] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register built-in tools. Subclasses can call register_tool() to add more."""
        from src.tools.search import web_search

        def _web_search_handler(tool_input: dict) -> str:
            results = web_search(tool_input["query"])
            trimmed = [
                {"title": r["title"], "url": r["url"], "snippet": r["snippet"][:200]}
                for r in results
            ]
            return json.dumps(trimmed)

        self.register_tool("web_search", _web_search_handler)

    def register_tool(self, name: str, handler: ToolHandler) -> None:
        """Register a new tool handler. Called by subclasses to extend tool support."""
        self._tool_handlers[name] = handler

    def _call_api(self, messages: list[dict]) -> anthropic.types.Message:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.system_prompt,
            "messages": messages,
        }
        if self.tools:
            kwargs["tools"] = self.tools
        return self.gatekeeper.execute(self._client.messages.create, **kwargs)

    def _handle_tool_use(self, response: anthropic.types.Message, depth: int = 0) -> str:
        """FIX #2: Uses self._tool_handlers dict instead of hardcoded if-blocks."""
        if depth >= self._max_tool_rounds:
            self.logger.warning(self.name, "Max tool rounds reached — extracting text as-is")
            return self._extract_text(response)

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                self.logger.info(self.name, f"Tool call: {block.name}({block.input})")
                handler = self._tool_handlers.get(block.name)
                if handler:
                    result_content = handler(block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_content,
                    })
                else:
                    self.logger.warning(self.name, f"Unknown tool: {block.name} — skipping")

        if not tool_results:
            return self._extract_text(response)

        self.history.append({"role": "assistant", "content": response.content})
        self.history.append({"role": "user", "content": tool_results})

        follow_up = self.watchdog.run(self._call_api, self.history, source=self.name)

        if follow_up.stop_reason == "tool_use":
            return self._handle_tool_use(follow_up, depth=depth + 1)

        return self._extract_text(follow_up)

    def _extract_text(self, response: anthropic.types.Message) -> str:
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""

    @staticmethod
    def _strip_markdown(text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.split("\n")
            inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            return "\n".join(inner).strip()
        return stripped

    def generate_response(self, user_message: str) -> str:
        """FIX #1 (SPOF): catches WatchdogTimeoutError and returns a safe fallback.

        The original code let WatchdogTimeoutError propagate to the debate orchestrator,
        which then caught it as a generic exception and awarded an incorrect verdict.
        Now the agent reports unavailability and the orchestrator can handle it gracefully.
        """
        self.history.append({"role": "user", "content": user_message})

        try:
            response = self.watchdog.run(self._call_api, self.history, source=self.name)
        except WatchdogTimeoutError as exc:
            self.logger.error(self.name, f"generate_response exhausted retries: {exc}")
            self.history.append({"role": "assistant", "content": _FALLBACK_RESPONSE})
            return _FALLBACK_RESPONSE

        self.logger.info(
            self.name,
            f"Tokens: in={response.usage.input_tokens} out={response.usage.output_tokens}",
        )

        if response.stop_reason == "tool_use":
            text = self._handle_tool_use(response)
        else:
            text = self._extract_text(response)

        text = self._strip_markdown(text)
        self.history.append({"role": "assistant", "content": text})
        return text
