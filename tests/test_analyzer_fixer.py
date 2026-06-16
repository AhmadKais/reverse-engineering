"""Unit tests for AnalyzerAgent and FixerAgent — no real API calls."""

from __future__ import annotations

import json
from unittest.mock import patch

from src.agents.analyzer_agent import AnalyzerAgent
from src.agents.base_agent import AgentBudget
from src.agents.fixer_agent import FixerAgent


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


class TestFixerAgent:
    def _make_agent(self) -> FixerAgent:
        budget = AgentBudget(max_tokens=10_000)
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            return FixerAgent(budget)

    def test_parse_valid_fix_report(self):
        agent = self._make_agent()
        raw = json.dumps({
            "fixes": [{
                "bug_type": "SPOF",
                "file_path": "polygons/polygons.py",
                "description": "Fix formula for polygon angles",
                "original_code": "class Polygon(Object):",
                "fixed_code": "class Polygon(object):",
                "explanation": "Wrong base class removed",
            }],
            "overall_impact": "Reduced coupling",
        })
        result = agent._parse_fixes(raw)
        assert len(result["fixes"]) == 1

    def test_apply_fixes_dry_run_produces_dry_run_lines(self, tmp_path):
        agent = self._make_agent()
        fix_report = {"fixes": [{
            "bug_type": "GodObject", "file_path": "mathsquiz/mathsquiz.py",
            "target_symbol": "mathsquiz", "description": "Extract questions into functions",
            "architectural_pattern": "Facade", "new_class_or_method": "ask_question",
            "explanation": "Reduces God Script responsibilities",
        }]}
        results = agent.apply_fixes(fix_report, str(tmp_path), dry_run=True)
        assert len(results) == 1
        assert "DRY-RUN" in results[0]
        assert "mathsquiz" in results[0]

    def test_apply_fixes_plan_mode_produces_plan_lines(self, tmp_path):
        agent = self._make_agent()
        fix_report = {"fixes": [{
            "bug_type": "LogicBug", "file_path": "polygons/polygons.py",
            "target_symbol": "draw_polygon", "description": "Fix hardcoded hexagon loop",
            "architectural_pattern": "Strategy", "new_class_or_method": "",
            "explanation": "Use sides from polygon_details",
        }]}
        results = agent.apply_fixes(fix_report, str(tmp_path), dry_run=False)
        assert len(results) == 1
        assert "PLAN" in results[0]

    def test_apply_fixes_returns_one_result_per_fix(self, tmp_path):
        agent = self._make_agent()
        fix_report = {"fixes": [
            {"bug_type": "SPOF", "file_path": "a.py", "target_symbol": "X",
             "description": "Fix A", "architectural_pattern": "Strategy",
             "new_class_or_method": "", "explanation": "x"},
            {"bug_type": "GodObject", "file_path": "b.py", "target_symbol": "Y",
             "description": "Fix B", "architectural_pattern": "Factory",
             "new_class_or_method": "", "explanation": "y"},
        ]}
        results = agent.apply_fixes(fix_report, str(tmp_path), dry_run=True)
        assert len(results) == 2

    def test_apply_fixes_empty_report(self, tmp_path):
        agent = self._make_agent()
        results = agent.apply_fixes({"fixes": []}, str(tmp_path), dry_run=True)
        assert results == []
