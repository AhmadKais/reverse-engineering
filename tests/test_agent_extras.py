"""Tests for AnalyzerAgent sparse fallback and FixerAgent affected-code reading."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.agents.base_agent import AgentBudget


class TestAnalyzerSparseFallback:
    def test_parse_error_triggers_fallback(self):
        from src.agents.analyzer_agent import AnalyzerAgent

        budget = AgentBudget(50_000)
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            agent = AnalyzerAgent(budget)
        result = agent._parse_report("I cannot parse this codebase.")
        assert result.get("parse_error") is True

    def test_embedded_json_is_extracted(self):
        from src.agents.analyzer_agent import AnalyzerAgent

        budget = AgentBudget(50_000)
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            agent = AnalyzerAgent(budget)
        raw = (
            'Some preamble text {"bugs": [{"type": "SPOF", "severity": "critical", '
            '"affected_nodes": ["A"], "evidence": "high betweenness", '
            '"fix_hint": "add backup"}], "summary": "Found one bug"} trailing text'
        )
        result = agent._parse_report(raw)
        assert len(result["bugs"]) == 1
        assert result["bugs"][0]["type"] == "SPOF"


class TestFixerAffectedCode:
    def test_reads_file_containing_class(self, tmp_path):
        from src.agents.fixer_agent import FixerAgent

        budget = AgentBudget(50_000)
        (tmp_path / "mymod.py").write_text("class MyTarget:\n    pass\n", encoding="utf-8")
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            agent = FixerAgent(budget)
        bugs = [{"affected_nodes": ["MyTarget"], "type": "GodObject"}]
        snippets = agent._read_affected_code(bugs, str(tmp_path))
        assert "MyTarget" in snippets or "mymod" in snippets

    def test_returns_no_code_message_when_not_found(self, tmp_path):
        from src.agents.fixer_agent import FixerAgent

        budget = AgentBudget(50_000)
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            agent = FixerAgent(budget)
        bugs = [{"affected_nodes": ["NonexistentClass"], "type": "SPOF"}]
        snippets = agent._read_affected_code(bugs, str(tmp_path))
        assert "No code files found" in snippets

    def test_skips_duplicate_files(self, tmp_path):
        from src.agents.fixer_agent import FixerAgent

        budget = AgentBudget(50_000)
        (tmp_path / "mymod.py").write_text(
            "class AlphaNode:\n    pass\nclass BetaNode:\n    pass\n",
            encoding="utf-8",
        )
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            agent = FixerAgent(budget)
        bugs = [
            {"affected_nodes": ["AlphaNode"], "type": "SPOF"},
            {"affected_nodes": ["BetaNode"], "type": "GodObject"},
        ]
        snippets = agent._read_affected_code(bugs, str(tmp_path))
        assert snippets.count("mymod.py") == 1
