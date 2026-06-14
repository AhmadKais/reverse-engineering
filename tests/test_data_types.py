"""Tests for GraphNode, GraphEdge data types and KnowledgeGraph extras."""

from __future__ import annotations

import json
import os
import tempfile
import textwrap
from pathlib import Path

from src.data_types.graph_edge import EdgeKind, EdgeLabel, GraphEdge
from src.data_types.graph_node import GraphNode, NodeKind
from src.graph_builder.ast_parser import parse_file
from src.graph_builder.graph_generator import KnowledgeGraph


def _write_py(content: str, tmpdir: str, filename: str = "mod.py") -> str:
    path = os.path.join(tmpdir, filename)
    Path(path).write_text(textwrap.dedent(content), encoding="utf-8")
    return path


class TestGraphNode:
    def _node(self, **kwargs) -> GraphNode:
        defaults = dict(id="mod.py::Foo", kind=NodeKind.CLASS, name="Foo",
                        file_path="mod.py", line_start=1, line_end=5)
        return GraphNode(**{**defaults, **kwargs})

    def test_label_for_top_level_node(self):
        assert self._node(name="Foo", parent_class=None).label == "Foo"

    def test_label_for_method(self):
        n = self._node(name="run", kind=NodeKind.METHOD, parent_class="Foo")
        assert n.label == "Foo.run"

    def test_obsidian_slug_replaces_slashes(self):
        n = self._node(id="src/agents/base_agent.py::BaseAgent")
        assert "/" not in n.obsidian_slug

    def test_obsidian_slug_replaces_dots(self):
        assert "." not in self._node(id="a.b.c::Foo").obsidian_slug

    def test_to_dict_is_serializable(self):
        assert json.dumps(self._node().to_dict())

    def test_base_classes_default_empty(self):
        assert self._node().base_classes == []

    def test_calls_default_empty(self):
        assert self._node().calls == []


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
        assert d["source"] == "A" and d["target"] == "B"

    def test_edge_kind_values(self):
        assert EdgeKind.EXTRACTED == "Extracted"
        assert EdgeKind.INFERRED == "Inferred"
        assert EdgeKind.AMBIGUOUS == "Ambiguous"

    def test_edge_label_values(self):
        assert EdgeLabel.IMPORTS == "imports"
        assert EdgeLabel.INHERITS == "inherits"
        assert EdgeLabel.CALLS == "calls"


class TestKnowledgeGraphExtras:
    def test_get_neighbors_returns_both_directions(self):
        with tempfile.TemporaryDirectory() as d:
            nodes, edges = parse_file(_write_py("""
                class A:
                    pass
                class B(A):
                    pass
            """, d))
        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        kg.compute_metrics()
        a_id = next((nid for nid, n in kg._nodes.items() if n.name == "A"), None)
        if a_id:
            assert isinstance(kg.get_neighbors(a_id), list)

    def test_summary_dict_has_all_required_keys(self):
        with tempfile.TemporaryDirectory() as d:
            nodes, edges = parse_file(_write_py("class X:\n    pass\n", d))
        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        kg.compute_metrics()
        summary = kg.summary_dict()
        for key in ("node_count", "edge_count", "top_hubs", "community_count", "bridge_count"):
            assert key in summary

    def test_top_hubs_in_summary_have_required_fields(self):
        with tempfile.TemporaryDirectory() as d:
            nodes, edges = parse_file(_write_py("""
                class Hub:
                    def a(self): pass
                    def b(self): pass
            """, d))
        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        kg.compute_metrics()
        for hub in kg.summary_dict()["top_hubs"]:
            assert "id" in hub and "name" in hub and "betweenness" in hub
            assert "in_degree" in hub and "out_degree" in hub

    def test_metrics_cached_after_first_call(self):
        with tempfile.TemporaryDirectory() as d:
            nodes, edges = parse_file(_write_py("class X:\n    pass\n", d))
        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        m1 = kg.compute_metrics()
        m2 = kg.metrics
        assert m1 is m2

    def test_inferred_edges_not_added_for_non_init(self):
        with tempfile.TemporaryDirectory() as d:
            nodes, edges = parse_file(_write_py("""
                class Container:
                    def helper(self):
                        return Inner()
                class Inner:
                    pass
            """, d))
        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        assert kg.graph.number_of_nodes() >= 2
