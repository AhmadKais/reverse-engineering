"""Unit tests for AgentBudget and BaseAgent — no real API calls.

See also: test_analyzer_fixer.py (AnalyzerAgent, FixerAgent)
          test_agent_extras.py (sparse-mode and affected-code tests)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.agents.base_agent import AgentBudget, BaseAgent, TokenBudgetExceededError


class TestAgentBudget:
    def test_initial_state(self):
        b = AgentBudget(max_tokens=1000)
        assert b.total_used == 0
        assert b.remaining == 1000

    def test_records_tokens(self):
        b = AgentBudget(max_tokens=1000)
        b.record(100, 200)
        assert b.used_input == 100
        assert b.used_output == 200
        assert b.total_used == 300
        assert b.remaining == 700

    def test_raises_on_budget_exceeded(self):
        b = AgentBudget(max_tokens=100)
        with pytest.raises(TokenBudgetExceededError):
            b.record(60, 60)

    def test_status_dict(self):
        b = AgentBudget(max_tokens=500)
        b.record(50, 50)
        s = b.status()
        assert s["total_used"] == 100
        assert s["budget"] == 500
        assert s["remaining"] == 400

    def test_budget_exactly_at_limit_does_not_raise(self):
        b = AgentBudget(max_tokens=100)
        b.record(50, 50)
        assert b.total_used == 100


class TestBaseAgent:
    def _make_agent(self) -> BaseAgent:
        budget = AgentBudget(max_tokens=10_000)
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            return BaseAgent(name="TestAgent", system_prompt="You are a test agent.", budget=budget)

    def test_history_empty_on_init(self):
        assert self._make_agent().history == []

    def test_reset_history(self):
        agent = self._make_agent()
        agent.history = [{"role": "user", "content": "hi"}]
        agent.reset_history()
        assert agent.history == []

    def test_generate_response_appends_to_history(self):
        agent = self._make_agent()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="test reply")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        with patch.object(agent._client.messages, "create", return_value=mock_response):
            reply = agent.generate_response("hello")
        assert reply == "test reply"
        assert len(agent.history) == 2
        assert agent.history[0] == {"role": "user", "content": "hello"}
        assert agent.history[1] == {"role": "assistant", "content": "test reply"}

    def test_budget_is_updated_after_call(self):
        agent = self._make_agent()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="answer")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        with patch.object(agent._client.messages, "create", return_value=mock_response):
            agent.generate_response("test")
        assert agent.budget.used_input == 100
        assert agent.budget.used_output == 50
