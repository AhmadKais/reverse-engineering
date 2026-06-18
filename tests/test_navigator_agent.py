"""Tests for NavigatorAgent."""

from __future__ import annotations

import tempfile
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.agents.base_agent import AgentBudget
from src.graph_builder.ast_parser import parse_file
from src.graph_builder.graph_generator import KnowledgeGraph


def _write_py(content: str, tmpdir: str, filename: str = "mod.py") -> str:
    path = str(Path(tmpdir) / filename)
    Path(path).write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def _make_simple_kg(source: str = "") -> KnowledgeGraph:
    if source:
        with tempfile.TemporaryDirectory() as d:
            nodes, edges = parse_file(_write_py(source, d))
    else:
        nodes, edges = [], []
    kg = KnowledgeGraph()
    kg.build(nodes, edges)
    kg.compute_metrics()
    return kg


class TestNavigatorAgent:
    def test_navigate_calls_llm_with_summary(self):
        from src.agents.navigator_agent import NavigatorAgent

        budget = AgentBudget(50_000)
        kg = _make_simple_kg("class Hub:\n    def run(self):\n        pass\n")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="## Architectural Overview\nSimple module.")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 30

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            agent = NavigatorAgent(budget)
            with patch.object(agent._client.messages, "create", return_value=mock_response):
                result = agent.navigate(kg)

        assert len(result) > 0
        assert budget.total_used == 130

    def test_navigate_resets_history_before_call(self):
        from src.agents.navigator_agent import NavigatorAgent

        budget = AgentBudget(50_000)
        kg = _make_simple_kg("x = 1\n")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="overview")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            agent = NavigatorAgent(budget)
            agent.history = [{"role": "user", "content": "stale message"}]
            with patch.object(agent._client.messages, "create", return_value=mock_response):
                agent.navigate(kg)

        assert len(agent.history) == 2
