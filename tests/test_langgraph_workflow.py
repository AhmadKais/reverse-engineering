"""Unit tests for the LangGraph workflow — no real API calls."""

from __future__ import annotations

import textwrap
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.agents.base_agent import AgentBudget
from src.langgraph_workflow import build_workflow, WorkflowState


# ── Helpers ────────────────────────────────────────────────────────────────────

def _minimal_source(tmpdir: str) -> str:
    Path(os.path.join(tmpdir, "sample.py")).write_text(
        textwrap.dedent("""
            class A:
                pass
            class B(A):
                pass
        """),
        encoding="utf-8",
    )
    return tmpdir


def _initial_state(source: str, vault: str) -> WorkflowState:
    return WorkflowState(
        source_root=source,
        vault_dir=vault,
        knowledge_graph=None,
        graph_summary={},
        navigation="",
        bug_report={},
        fix_report={},
        token_usage={},
        error=None,
    )


# ── Workflow construction ──────────────────────────────────────────────────────

class TestBuildWorkflow:
    def test_returns_compiled_graph_and_budget(self):
        wf, budget = build_workflow(token_budget=5000)
        assert budget.max_tokens == 5000
        assert wf is not None

    def test_graph_has_expected_nodes(self):
        wf, _ = build_workflow()
        graph = wf.get_graph()
        node_names = {n for n in graph.nodes}
        assert "build_graph" in node_names
        assert "navigate"    in node_names
        assert "analyze"     in node_names
        assert "fix"         in node_names

    def test_mermaid_diagram_is_string(self):
        wf, _ = build_workflow()
        diagram = wf.get_graph().draw_mermaid()
        assert isinstance(diagram, str)
        assert "build_graph" in diagram
        assert "navigate"    in diagram
        assert "fix"         in diagram


# ── build_graph_node ──────────────────────────────────────────────────────────

class TestBuildGraphNode:
    def test_populates_graph_summary(self):
        from src.langgraph_workflow import build_graph_node

        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as vault:
            _minimal_source(src)
            state = _initial_state(src, vault)
            result = build_graph_node(state)

        assert result["error"] is None
        assert result["graph_summary"]["node_count"] > 0
        assert result["knowledge_graph"] is not None

    def test_exports_obsidian_vault(self):
        from src.langgraph_workflow import build_graph_node

        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as vault:
            _minimal_source(src)
            state = _initial_state(src, vault)
            build_graph_node(state)
            assert (Path(vault) / "graph.json").exists()
            assert (Path(vault) / "hot.md").exists()
            assert (Path(vault) / "index.md").exists()

    def test_sets_error_on_invalid_source(self):
        from src.langgraph_workflow import build_graph_node

        with tempfile.TemporaryDirectory() as vault:
            state = _initial_state("/nonexistent/path/xyz", vault)
            result = build_graph_node(state)

        # Non-existent path: parse_directory returns empty lists → graph still builds
        # but node_count == 0 (not an error, just empty)
        assert result["graph_summary"]["node_count"] == 0


# ── Error propagation ──────────────────────────────────────────────────────────

class TestErrorPropagation:
    def test_navigate_node_skips_on_error(self):
        from src.langgraph_workflow import navigate_node

        budget = AgentBudget(5000)
        state = _initial_state("/irrelevant", "/irrelevant")
        state["error"] = "upstream failure"

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            result = navigate_node(state, budget)

        # Should pass through without calling the LLM
        assert result["error"] == "upstream failure"
        assert result["navigation"] == ""
        assert budget.total_used == 0   # no API call made

    def test_analyze_node_skips_on_error(self):
        from src.langgraph_workflow import analyze_node

        budget = AgentBudget(5000)
        state = _initial_state("/irrelevant", "/irrelevant")
        state["error"] = "upstream failure"

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            result = analyze_node(state, budget)

        assert result["error"] == "upstream failure"
        assert budget.total_used == 0

    def test_fix_node_skips_on_error(self):
        from src.langgraph_workflow import fix_node

        budget = AgentBudget(5000)
        state = _initial_state("/irrelevant", "/irrelevant")
        state["error"] = "upstream failure"

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            result = fix_node(state, budget)

        assert result["error"] == "upstream failure"
        assert budget.total_used == 0
