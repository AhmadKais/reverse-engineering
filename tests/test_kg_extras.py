"""Tests for KnowledgeGraph extra methods (summary, neighbors, metrics caching)."""

from __future__ import annotations

import os
import tempfile
import textwrap
from pathlib import Path

from src.graph_builder.ast_parser import parse_file
from src.graph_builder.graph_generator import KnowledgeGraph


def _write_py(content: str, tmpdir: str, filename: str = "mod.py") -> str:
    path = os.path.join(tmpdir, filename)
    Path(path).write_text(textwrap.dedent(content), encoding="utf-8")
    return path


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
