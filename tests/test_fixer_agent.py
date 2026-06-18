"""Unit tests for FixerAgent — no real API calls."""

from __future__ import annotations

import json
from unittest.mock import patch

from src.agents.base_agent import AgentBudget
from src.agents.fixer_agent import FixerAgent


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

    def test_parse_corrected_files_two_files(self):
        agent = self._make_agent()
        raw = (
            "FILE: polygons/polygons.py\n"
            "---BEGIN---\n"
            "class Polygon(object):\n"
            "    pass\n"
            "---END---\n"
            "FILE: mathsquiz/mathsquiz.py\n"
            "---BEGIN---\n"
            "print('hello')\n"
            "---END---\n"
        )
        result = agent._parse_corrected_files(raw)
        assert "polygons/polygons.py" in result
        assert "mathsquiz/mathsquiz.py" in result
        assert "class Polygon(object)" in result["polygons/polygons.py"]
        assert "print('hello')" in result["mathsquiz/mathsquiz.py"]

    def test_parse_corrected_files_empty_returns_empty(self):
        agent = self._make_agent()
        result = agent._parse_corrected_files("no files here")
        assert result == {}

    def test_generate_corrected_files_no_bugs_returns_empty(self):
        agent = self._make_agent()
        result = agent.generate_corrected_files({"bugs": []}, {"a.py": "x = 1"})
        assert result == {}

    def test_generate_corrected_files_calls_llm(self):
        agent = self._make_agent()
        mock_response = (
            "FILE: mathsquiz/mathsquiz.py\n"
            "---BEGIN---\n"
            "print('fixed')\n"
            "---END---\n"
        )
        with patch.object(agent, "generate_response", return_value=mock_response):
            result = agent.generate_corrected_files(
                {"bugs": [{"type": "SyntaxError", "affected_nodes": ["mathsquiz.py"]}]},
                {"mathsquiz/mathsquiz.py": "print 'broken'"},
            )
        assert "mathsquiz/mathsquiz.py" in result
        assert "print('fixed')" in result["mathsquiz/mathsquiz.py"]
