"""Tests for GraphNode and GraphEdge data types."""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path

from src.data_types.graph_edge import EdgeKind, EdgeLabel, GraphEdge
from src.data_types.graph_node import GraphNode, NodeKind


def _write_py(content: str, tmpdir: str, filename: str = "mod.py") -> str:
    path = os.path.join(tmpdir, filename)
    Path(path).write_text(textwrap.dedent(content), encoding="utf-8")
    return path


class TestGraphNode:
    def _node(self, **kwargs) -> GraphNode:
        defaults = {"id": "mod.py::Foo", "kind": NodeKind.CLASS, "name": "Foo",
                    "file_path": "mod.py", "line_start": 1, "line_end": 5}
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

    def test_edge_default_confidence(self):
        e = GraphEdge(source="A", target="B", kind=EdgeKind.EXTRACTED, label=EdgeLabel.CALLS)
        assert e.confidence == 1.0

    def test_edge_custom_confidence(self):
        e = GraphEdge(source="A", target="B", kind=EdgeKind.INFERRED,
                      label=EdgeLabel.COMPOSES, confidence=0.8)
        assert e.confidence == 0.8

    def test_edge_source_file_default_empty(self):
        e = GraphEdge(source="A", target="B", kind=EdgeKind.EXTRACTED, label=EdgeLabel.IMPORTS)
        assert e.source_file == ""

    def test_edge_source_file_stored(self):
        e = GraphEdge(source="A", target="B", kind=EdgeKind.EXTRACTED,
                      label=EdgeLabel.CALLS, source_file="src/mod.py")
        assert e.source_file == "src/mod.py"

    def test_edge_to_dict_includes_confidence_and_source_file(self):
        e = GraphEdge(source="A", target="B", kind=EdgeKind.EXTRACTED,
                      label=EdgeLabel.CALLS, confidence=0.9, source_file="x.py")
        d = e.to_dict()
        assert d["confidence"] == 0.9
        assert d["source_file"] == "x.py"
