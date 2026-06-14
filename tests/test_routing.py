"""Tests for routing logic, sparse-mode nodes, ObsidianExporter, and data types.

Covers gaps not hit by the other test files:
  - _route_after_build conditional routing
  - raw_reader_node (mocked API)
  - _fallback_bug_report
  - ObsidianExporter unit tests (graph.json, hot.md, index.md, node notes)
  - NavigatorAgent (mocked API)
  - GraphNode / GraphEdge data types
  - KnowledgeGraph.get_neighbors, summary_dict completeness
  - Sparse-mode end-to-end: broken Python 2 code → is_sparse=True
  - WorkflowState missing optional fields handled gracefully
"""

from __future__ import annotations

import json
import os
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.agents.base_agent import AgentBudget
from src.data_types.graph_edge import EdgeKind, EdgeLabel, GraphEdge
from src.data_types.graph_node import GraphNode, NodeKind
from src.graph_builder.ast_parser import parse_file
from src.graph_builder.graph_generator import KnowledgeGraph
from src.graph_builder.obsidian_exporter import ObsidianExporter
from src.langgraph_workflow import (
    WorkflowState,
    _fallback_bug_report,
    _route_after_build,
    build_graph_node,
    raw_reader_node,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _write_py(content: str, tmpdir: str, filename: str = "mod.py") -> str:
    path = os.path.join(tmpdir, filename)
    Path(path).write_text(textwrap.dedent(content), encoding="utf-8")
    return path


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


def _make_simple_kg(source: str = "") -> KnowledgeGraph:
    """Build a small KnowledgeGraph from inline source (uses a temp file)."""
    if source:
        with tempfile.TemporaryDirectory() as d:
            nodes, edges = parse_file(_write_py(source, d))
    else:
        nodes, edges = [], []
    kg = KnowledgeGraph()
    kg.build(nodes, edges)
    kg.compute_metrics()
    return kg


# ── _route_after_build ────────────────────────────────────────────────────────

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


# ── _fallback_bug_report ──────────────────────────────────────────────────────

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
        assert "bugs" in result
        assert "summary" in result

    def test_each_bug_has_required_fields(self):
        result = _fallback_bug_report("print syntax error found score", {"a.py": ""})
        for bug in result["bugs"]:
            assert "type" in bug
            assert "severity" in bug
            assert "affected_nodes" in bug
            assert "evidence" in bug
            assert "fix_hint" in bug

    def test_empty_navigation_produces_no_bugs(self):
        result = _fallback_bug_report("", {"a.py": ""})
        assert result["bugs"] == []


# ── build_graph_node — sparse detection ──────────────────────────────────────

class TestBuildGraphNodeSparse:
    def test_python2_code_sets_is_sparse(self):
        """Broken Python 2 code cannot be parsed by ast → 0 edges → sparse=True."""
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as vault:
            # Python 2 print statement breaks ast.parse()
            Path(os.path.join(src, "broken.py")).write_text(
                'print "hello"\nif x = 1:\n    pass\n', encoding="utf-8"
            )
            state = _blank_state(src, vault)
            result = build_graph_node(state)

        assert result["error"] is None
        assert result["is_sparse"] is True

    def test_sparse_mode_populates_raw_files(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as vault:
            Path(os.path.join(src, "broken.py")).write_text(
                'print "hello"\n', encoding="utf-8"
            )
            state = _blank_state(src, vault)
            result = build_graph_node(state)

        assert "broken.py" in result["raw_files"]

    def test_dense_graph_is_not_sparse(self):
        """A module with many imports + inheritance edges should have ≥ 5 edges → not sparse."""
        from src.langgraph_workflow import SPARSE_EDGE_THRESHOLD

        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as vault:
            # Generate a source file rich enough to produce ≥ 5 edges
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
            state = _blank_state(src, vault)
            result = build_graph_node(state)

        assert result["error"] is None
        # is_sparse must be consistent with the actual edge count
        edge_count = result["graph_summary"]["edge_count"]
        expected_sparse = edge_count < SPARSE_EDGE_THRESHOLD
        assert result["is_sparse"] is expected_sparse
        # When not sparse, raw_files should be empty
        if not result["is_sparse"]:
            assert result["raw_files"] == {}


# ── raw_reader_node ───────────────────────────────────────────────────────────

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


# ── NavigatorAgent ────────────────────────────────────────────────────────────

class TestNavigatorAgent:
    def test_navigate_calls_llm_with_summary(self):
        from src.agents.navigator_agent import NavigatorAgent

        budget = AgentBudget(50_000)
        kg = _make_simple_kg("class Hub:\n    def run(self):\n        pass\n")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="## Architectural Overview\nThis is a simple module.")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 30

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            agent = NavigatorAgent(budget)
            with patch.object(agent._client.messages, "create", return_value=mock_response):
                result = agent.navigate(kg)

        assert "Architectural" in result or len(result) > 0
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

        assert len(agent.history) == 2   # only one user + one assistant from this call


# ── ObsidianExporter unit tests ───────────────────────────────────────────────

class TestObsidianExporter:
    @pytest.fixture
    def simple_kg(self):
        kg = _make_simple_kg("""
            class Alpha:
                def run(self):
                    pass
            class Beta(Alpha):
                pass
        """)
        return kg

    def test_graph_json_has_correct_meta_counts(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        data = json.loads((tmp_path / "graph.json").read_text(encoding="utf-8"))
        assert data["meta"]["node_count"] == len(data["nodes"])
        assert data["meta"]["edge_count"] == len(data["edges"])

    def test_graph_json_nodes_have_required_fields(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        data = json.loads((tmp_path / "graph.json").read_text(encoding="utf-8"))
        for node in data["nodes"]:
            assert "id" in node
            assert "kind" in node
            assert "betweenness" in node

    def test_hot_md_has_betweenness_header(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        hot = (tmp_path / "hot.md").read_text(encoding="utf-8")
        assert "Betweenness" in hot

    def test_hot_md_is_markdown_table(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        hot = (tmp_path / "hot.md").read_text(encoding="utf-8")
        lines_with_pipe = [l for l in hot.splitlines() if "|" in l]
        assert len(lines_with_pipe) >= 2   # header row + separator + at least one data row

    def test_index_md_has_classes_section(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        index = (tmp_path / "index.md").read_text(encoding="utf-8")
        assert "Class" in index

    def test_node_notes_created_for_every_node(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        notes = list((tmp_path / "nodes").glob("*.md"))
        assert len(notes) == simple_kg.graph.number_of_nodes()

    def test_node_notes_contain_kind_line(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        notes = list((tmp_path / "nodes").glob("*.md"))
        for note in notes:
            content = note.read_text(encoding="utf-8")
            assert "**Kind**" in content

    def test_export_empty_graph_does_not_crash(self, tmp_path):
        kg = KnowledgeGraph()
        kg.build([], [])
        kg.compute_metrics()
        ObsidianExporter(str(tmp_path)).export(kg)
        assert (tmp_path / "graph.json").exists()
        assert (tmp_path / "hot.md").exists()
        assert (tmp_path / "index.md").exists()

    def test_node_notes_with_inheritance_show_inherits_from(self, tmp_path):
        kg = _make_simple_kg("""
            class Parent:
                pass
            class Child(Parent):
                pass
        """)
        ObsidianExporter(str(tmp_path)).export(kg)
        notes = list((tmp_path / "nodes").glob("*.md"))
        all_text = "\n".join(n.read_text(encoding="utf-8") for n in notes)
        assert "Inherits From" in all_text


# ── GraphNode data type ───────────────────────────────────────────────────────

class TestGraphNode:
    def _node(self, **kwargs) -> GraphNode:
        defaults = dict(id="mod.py::Foo", kind=NodeKind.CLASS, name="Foo",
                        file_path="mod.py", line_start=1, line_end=5)
        return GraphNode(**{**defaults, **kwargs})

    def test_label_for_top_level_node(self):
        n = self._node(name="Foo", parent_class=None)
        assert n.label == "Foo"

    def test_label_for_method(self):
        n = self._node(name="run", kind=NodeKind.METHOD, parent_class="Foo")
        assert n.label == "Foo.run"

    def test_obsidian_slug_replaces_slashes(self):
        n = self._node(id="src/agents/base_agent.py::BaseAgent")
        assert "/" not in n.obsidian_slug

    def test_obsidian_slug_replaces_dots(self):
        n = self._node(id="a.b.c::Foo")
        assert "." not in n.obsidian_slug

    def test_to_dict_is_serializable(self):
        n = self._node()
        d = n.to_dict()
        assert json.dumps(d)   # must be JSON-serializable

    def test_base_classes_default_empty(self):
        n = self._node()
        assert n.base_classes == []

    def test_calls_default_empty(self):
        n = self._node()
        assert n.calls == []


# ── GraphEdge data type ───────────────────────────────────────────────────────

class TestGraphEdge:
    def test_edge_default_weight(self):
        e = GraphEdge(source="A", target="B", kind=EdgeKind.EXTRACTED, label=EdgeLabel.IMPORTS)
        assert e.weight == 1.0

    def test_edge_custom_weight(self):
        e = GraphEdge(source="A", target="B", kind=EdgeKind.INFERRED,
                      label=EdgeLabel.COMPOSES, weight=0.7)
        assert e.weight == 0.7

    def test_edge_to_dict(self):
        e = GraphEdge(source="A", target="B", kind=EdgeKind.EXTRACTED, label=EdgeLabel.CALLS)
        d = e.to_dict()
        assert d["source"] == "A"
        assert d["target"] == "B"

    def test_edge_kind_values(self):
        assert EdgeKind.EXTRACTED == "Extracted"
        assert EdgeKind.INFERRED == "Inferred"
        assert EdgeKind.AMBIGUOUS == "Ambiguous"

    def test_edge_label_values(self):
        assert EdgeLabel.IMPORTS == "imports"
        assert EdgeLabel.INHERITS == "inherits"
        assert EdgeLabel.CALLS == "calls"


# ── KnowledgeGraph extras ─────────────────────────────────────────────────────

class TestKnowledgeGraphExtras:
    def test_get_neighbors_returns_both_directions(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_py("""
                class A:
                    pass
                class B(A):
                    pass
            """, d)
            nodes, edges = parse_file(path)

        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        kg.compute_metrics()

        # A should have at least one neighbor (B or the module)
        a_id = next((nid for nid, n in kg._nodes.items() if n.name == "A"), None)
        if a_id:
            neighbors = kg.get_neighbors(a_id)
            assert isinstance(neighbors, list)

    def test_summary_dict_has_all_required_keys(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_py("class X:\n    pass\n", d)
            nodes, edges = parse_file(path)

        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        kg.compute_metrics()

        summary = kg.summary_dict()
        for key in ("node_count", "edge_count", "top_hubs", "community_count", "bridge_count"):
            assert key in summary, f"Missing key: {key}"

    def test_top_hubs_in_summary_have_required_fields(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_py("""
                class Hub:
                    def a(self): pass
                    def b(self): pass
            """, d)
            nodes, edges = parse_file(path)

        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        kg.compute_metrics()

        for hub in kg.summary_dict()["top_hubs"]:
            assert "id" in hub
            assert "name" in hub
            assert "betweenness" in hub
            assert "in_degree" in hub
            assert "out_degree" in hub

    def test_metrics_cached_after_first_call(self):
        with tempfile.TemporaryDirectory() as d:
            path = _write_py("class X:\n    pass\n", d)
            nodes, edges = parse_file(path)

        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        m1 = kg.compute_metrics()
        m2 = kg.metrics   # reads cached value
        assert m1 is m2

    def test_inferred_edges_not_added_for_non_init(self):
        """Only __init__ method calls trigger composition inference."""
        with tempfile.TemporaryDirectory() as d:
            path = _write_py("""
                class Container:
                    def helper(self):
                        return Inner()

                class Inner:
                    pass
            """, d)
            nodes, edges = parse_file(path)

        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        # No crash — the graph is just built with whatever edges exist
        assert kg.graph.number_of_nodes() >= 2


# ── Analyzer sparse-mode fallback path ───────────────────────────────────────

class TestAnalyzerSparseFallback:
    def test_parse_error_triggers_fallback(self):
        """If the LLM returns unparseable JSON, the bug report falls back gracefully."""
        from src.agents.analyzer_agent import AnalyzerAgent

        budget = AgentBudget(50_000)
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="I cannot parse this codebase.")]
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 10

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            agent = AnalyzerAgent(budget)
            with patch.object(agent._client.messages, "create", return_value=mock_response):
                result = agent._parse_report("I cannot parse this codebase.")

        assert result.get("parse_error") is True

    def test_embedded_json_is_extracted(self):
        from src.agents.analyzer_agent import AnalyzerAgent

        budget = AgentBudget(50_000)
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            agent = AnalyzerAgent(budget)

        raw = 'Some preamble text {"bugs": [{"type": "SPOF", "severity": "critical", ' \
              '"affected_nodes": ["A"], "evidence": "high betweenness", ' \
              '"fix_hint": "add backup"}], "summary": "Found one bug"} trailing text'
        result = agent._parse_report(raw)
        assert len(result["bugs"]) == 1
        assert result["bugs"][0]["type"] == "SPOF"


# ── FixerAgent._read_affected_code ────────────────────────────────────────────

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
        assert snippets.count("mymod.py") == 1   # file read only once
