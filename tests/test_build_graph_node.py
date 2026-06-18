"""Tests for build_graph_node (sparse detection) and raw_reader_node."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.agents.base_agent import AgentBudget
from src.langgraph_workflow import (
    WorkflowState,
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


class TestBuildGraphNodeSparse:
    def test_python2_code_sets_is_sparse(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as vault:
            Path(os.path.join(src, "broken.py")).write_text(
                'print "hello"\nif x = 1:\n    pass\n', encoding="utf-8"
            )
            result = build_graph_node(_blank_state(src, vault))
        assert result["error"] is None
        assert result["is_sparse"] is True

    def test_sparse_mode_populates_raw_files(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as vault:
            Path(os.path.join(src, "broken.py")).write_text(
                'print "hello"\n', encoding="utf-8"
            )
            result = build_graph_node(_blank_state(src, vault))
        assert "broken.py" in result["raw_files"]

    def test_dense_graph_is_not_sparse(self):
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
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}), \
             patch("anthropic.Anthropic") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_response
            result = raw_reader_node(state, budget)
        assert result["navigation"] != ""
        assert result["error"] is None
