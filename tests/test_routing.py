"""Tests for routing logic and fallback bug report generation."""

from __future__ import annotations

from src.langgraph_workflow import (
    WorkflowState,
    _fallback_bug_report,
    _route_after_build,
)


def _blank_state(source: str = "/dev/null", vault: str = "/dev/null") -> WorkflowState:
    return WorkflowState(
        source_root=source,
        vault_dir=vault,
        knowledge_graph=None,
        graph_summary={},
        raw_files={},
        navigation="",
        bug_report={},
        fix_report={},
        token_usage={},
        is_sparse=False,
        error=None,
    )


class TestRouteAfterBuild:
    def test_routes_to_navigate_when_dense(self):
        state = _blank_state()
        state["is_sparse"] = False
        assert _route_after_build(state) == "navigate"

    def test_routes_to_raw_reader_when_sparse(self):
        state = _blank_state()
        state["is_sparse"] = True
        assert _route_after_build(state) == "raw_reader"

    def test_routes_to_analyze_on_error(self):
        state = _blank_state()
        state["error"] = "something exploded"
        assert _route_after_build(state) == "analyze"

    def test_error_takes_precedence_over_sparse(self):
        state = _blank_state()
        state["is_sparse"] = True
        state["error"] = "build failed"
        assert _route_after_build(state) == "analyze"


class TestFallbackBugReport:
    def test_generates_syntax_bug_on_print_keyword(self):
        result = _fallback_bug_report("print statement found, syntax error", {"a.py": ""})
        assert any(b["type"] == "SyntaxError" for b in result["bugs"])

    def test_generates_oop_bug_on_new_keyword(self):
        result = _fallback_bug_report("new object and class Object found", {"a.py": ""})
        assert any(b["type"] == "OOPBug" for b in result["bugs"])

    def test_generates_logic_bug_on_score_keyword(self):
        result = _fallback_bug_report("score is never incremented, answer is wrong", {"a.py": ""})
        assert any(b["type"] == "LogicBug" for b in result["bugs"])

    def test_returns_dict_with_bugs_key(self):
        result = _fallback_bug_report("nothing special here", {"a.py": ""})
        assert "bugs" in result and "summary" in result

    def test_each_bug_has_required_fields(self):
        result = _fallback_bug_report("print syntax error found score", {"a.py": ""})
        for bug in result["bugs"]:
            for field in ("type", "severity", "affected_nodes", "evidence", "fix_hint"):
                assert field in bug

    def test_empty_navigation_produces_no_bugs(self):
        result = _fallback_bug_report("", {"a.py": ""})
        assert result["bugs"] == []
