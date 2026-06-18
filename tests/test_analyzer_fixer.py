"""Unit tests for AnalyzerAgent — no real API calls."""

from __future__ import annotations

import json
from unittest.mock import patch

from src.agents.analyzer_agent import AnalyzerAgent
from src.agents.base_agent import AgentBudget


class TestAnalyzerAgent:
    def _make_agent(self) -> AnalyzerAgent:
        budget = AgentBudget(max_tokens=10_000)
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            return AnalyzerAgent(budget)

    def test_parse_valid_json(self):
        agent = self._make_agent()
        raw = json.dumps({
            "bugs": [{"type": "SPOF", "severity": "critical",
                      "affected_nodes": ["calc_polygon_details"],
                      "evidence": "high betweenness", "fix_hint": "add fallback"}],
            "summary": "One SPOF found.",
        })
        result = agent._parse_report(raw)
        assert len(result["bugs"]) == 1
        assert result["bugs"][0]["type"] == "SPOF"

    def test_parse_embedded_json(self):
        agent = self._make_agent()
        raw = 'Here is the analysis: {"bugs": [], "summary": "none found"}'
        result = agent._parse_report(raw)
        assert result["bugs"] == []

    def test_parse_malformed_returns_error_flag(self):
        agent = self._make_agent()
        result = agent._parse_report("this is not json")
        assert result.get("parse_error") is True

    def test_parse_empty_bugs_list(self):
        agent = self._make_agent()
        raw = '{"bugs": [], "summary": "clean architecture"}'
        result = agent._parse_report(raw)
        assert result["bugs"] == []
        assert result["summary"] == "clean architecture"
