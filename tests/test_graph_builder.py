"""Unit tests for the KnowledgeGraph class.

See also: test_ast_parser.py (parse_file / parse_directory)
"""

from __future__ import annotations

import json
import os
import tempfile
import textwrap
from pathlib import Path

import pytest

from src.data_types.graph_edge import EdgeKind, EdgeLabel
from src.data_types.graph_node import NodeKind
from src.graph_builder.ast_parser import parse_directory, parse_file
from src.graph_builder.graph_generator import KnowledgeGraph


def write_temp_py(content: str, filename: str = "test_module.py") -> str:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, filename)
    Path(path).write_text(textwrap.dedent(content), encoding="utf-8")
    return path


class TestKnowledgeGraph:
    def _make_kg_from_source(self, source: str) -> KnowledgeGraph:
        path = write_temp_py(source)
        nodes, edges = parse_file(path)
        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        return kg

    def test_graph_has_nodes(self):
        kg = self._make_kg_from_source("class A:\n    pass\nclass B(A):\n    pass\n")
        assert kg.graph.number_of_nodes() > 0

    def test_computes_metrics(self):
        kg = self._make_kg_from_source(
            "class Hub:\n    def method_a(self): pass\n    def method_b(self): pass\n"
            "class Worker(Hub):\n    pass\n"
        )
        m = kg.compute_metrics()
        assert m.node_count > 0
        assert isinstance(m.betweenness, dict)
        assert isinstance(m.top_hubs, list)

    def test_top_hubs_are_sorted_descending(self):
        kg = self._make_kg_from_source(
            "class A:\n    pass\nclass B(A):\n    pass\nclass C(B):\n    pass\n"
        )
        m = kg.compute_metrics()
        scores = [score for _, score in m.top_hubs]
        assert scores == sorted(scores, reverse=True)

    def test_summary_dict_is_serializable(self):
        kg = self._make_kg_from_source("class X:\n    pass\n")
        kg.compute_metrics()
        assert json.dumps(kg.summary_dict())

    def test_community_detection_runs(self):
        kg = self._make_kg_from_source(
            "class A:\n    pass\nclass B(A):\n    pass\nclass C:\n    pass\n"
        )
        m = kg.compute_metrics()
        assert isinstance(m.communities, list)

    def test_get_node_returns_none_for_unknown(self):
        kg = self._make_kg_from_source("x = 1\n")
        assert kg.get_node("nonexistent::id") is None

    def test_build_with_real_broken_python(self):
        broken_src = Path(__file__).parent.parent / "data" / "broken-python"
        if not broken_src.exists():
            pytest.skip("broken-python source not found")
        nodes, edges = parse_directory(str(broken_src))
        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        m = kg.compute_metrics()
        assert m.node_count >= 5
