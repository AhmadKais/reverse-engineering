"""Tests for routing logic, sparse detection, build_graph_node, and raw_reader_node.

See also: test_obsidian.py (ObsidianExporter, NavigatorAgent)
          test_data_types.py (GraphNode, GraphEdge, KnowledgeGraphExtras)
          test_agent_extras.py (AnalyzerSparseFallback, FixerAffectedCode)
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.agents.base_agent import AgentBudget
from src.langgraph_workflow import (
    WorkflowState,
    _fallback_bug_report,
    _route_after_build,
    build_graph_node,
    raw_reader_node,
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


class TestBuildGraphNodeSparse:
    def test_python2_code_sets_is_sparse(self):
        import tempfile
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as vault:
            Path(os.path.join(src, "broken.py")).write_text(
                'print "hello"\nif x = 1:\n    pass\n', encoding="utf-8"
            )
            result = build_graph_node(_blank_state(src, vault))
        assert result["error"] is None
        assert result["is_sparse"] is True

    def test_sparse_mode_populates_raw_files(self):
        import tempfile
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as vault:
            Path(os.path.join(src, "broken.py")).write_text(
                'print "hello"\n', encoding="utf-8"
            )
            result = build_graph_node(_blank_state(src, vault))
        assert "broken.py" in result["raw_files"]

    def test_dense_graph_is_not_sparse(self):
        import tempfile
        from src.langgraph_workflow import SPARSE_EDGE_THRESHOLD
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as vault:
            Path(os.path.join(src, "models.py")).write_text(
                "\n".join([
                    "import os, sys, json, re, pathlib",
                    "from collections import defaultdict",
                    "class Base:",
                    "    def run(self): pass",
                    "class Child(Base):",
                    "    def run(self): super().run()",
                    "class Worker(Child):",
                    "    pass",
                ]),
                encoding="utf-8",
            )
            result = build_graph_node(_blank_state(src, vault))
        assert result["error"] is None
        edge_count = result["graph_summary"]["edge_count"]
        assert result["is_sparse"] is (edge_count < SPARSE_EDGE_THRESHOLD)
        if not result["is_sparse"]:
            assert result["raw_files"] == {}


class TestRawReaderNode:
    def _patched_state(self) -> WorkflowState:
        state = _blank_state()
        state["is_sparse"] = True
        state["raw_files"] = {"broken.py": 'print "hello"\n'}
        return state

    def test_skips_on_error(self):
        budget = AgentBudget(5000)
        state = _blank_state()
        state["error"] = "upstream failure"
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            result = raw_reader_node(state, budget)
        assert result["error"] == "upstream failure"
        assert budget.total_used == 0

    def test_calls_llm_and_sets_navigation(self):
        budget = AgentBudget(50_000)
        state = self._patched_state()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="## File: broken.py\n**Intent**: a quiz\n")]
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 20
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("anthropic.Anthropic") as MockClient:
                MockClient.return_value.messages.create.return_value = mock_response
                result = raw_reader_node(state, budget)
        assert result["navigation"] != ""
        assert result["error"] is None
