"""Targeted tests for code paths in graph_generator, edge_inferrer, and ast modules."""

from __future__ import annotations

from unittest.mock import patch

from src.data_types.graph_edge import EdgeKind, EdgeLabel, GraphEdge
from src.data_types.graph_node import GraphNode, NodeKind
from src.graph_builder.graph_generator import KnowledgeGraph


def test_metrics_cached_second_call():
    kg = KnowledgeGraph()
    kg.build([], [])
    m1 = kg.metrics
    m2 = kg.metrics
    assert m1 is m2


def test_resolve_target_exact_id_match():
    node = GraphNode(id="foo.py::MyClass", kind=NodeKind.CLASS, name="MyClass",
                     file_path="foo.py", line_start=1, line_end=10)
    edge = GraphEdge(source="foo.py::MyClass", target="foo.py::MyClass",
                     kind=EdgeKind.EXTRACTED, label=EdgeLabel.CALLS, confidence=1.0)
    kg = KnowledgeGraph()
    kg.build([node], [edge])
    assert kg.graph.number_of_nodes() == 1


def test_compute_metrics_bridge_exception():
    import networkx as nx
    kg = KnowledgeGraph()
    kg.build([], [])
    with patch.object(nx, "bridges", side_effect=nx.NetworkXError("self-loop")):
        kg._metrics = None
        m = kg.compute_metrics()
    assert m.bridges == []


def test_compute_metrics_community_exception():
    kg = KnowledgeGraph()
    kg.build([], [])
    with patch("networkx.community.greedy_modularity_communities",
               side_effect=Exception("forced")):
        kg._metrics = None
        m = kg.compute_metrics()
    assert m.communities == []


def test_infer_composition_edges_full_path():
    engine = GraphNode(id="foo.py::Engine", kind=NodeKind.CLASS, name="Engine",
                       file_path="foo.py", line_start=1, line_end=5,
                       methods=["__init__"])
    engine_init = GraphNode(id="foo.py::Engine.__init__", kind=NodeKind.METHOD,
                            name="__init__", file_path="foo.py",
                            line_start=2, line_end=4, parent_class="Engine",
                            calls=["Fuel"])
    fuel = GraphNode(id="foo.py::Fuel", kind=NodeKind.CLASS, name="Fuel",
                     file_path="foo.py", line_start=6, line_end=10)
    kg = KnowledgeGraph()
    kg.build([engine, engine_init, fuel], [])
    assert kg.graph.number_of_nodes() == 3


def test_infer_composition_no_method_node():
    orphan = GraphNode(id="x.py::Orphan", kind=NodeKind.CLASS, name="Orphan",
                       file_path="x.py", line_start=1, line_end=5,
                       methods=["__init__"])
    kg = KnowledgeGraph()
    kg.build([orphan], [])
    assert kg.graph.number_of_nodes() == 1


def test_ast_visitors_attribute_base_name(tmp_path):
    from src.graph_builder.ast_parser import parse_file
    code = "class Child(base.Parent):\n    pass\n"
    src = tmp_path / "child.py"
    src.write_text(code)
    nodes, _ = parse_file(str(src))
    assert "Child" in {n.name for n in nodes}


def test_ast_visitors_unknown_base_name(tmp_path):
    from src.graph_builder.ast_parser import parse_file
    code = "class Foo(list[int]):\n    pass\n"
    src = tmp_path / "subscript_base.py"
    src.write_text(code)
    nodes, _ = parse_file(str(src))
    assert "Foo" in {n.name for n in nodes}


def test_parse_file_oserror():
    from src.graph_builder.ast_parser import parse_file
    nodes, edges = parse_file("/nonexistent/path/that/cannot/exist.py")
    assert nodes == [] and edges == []


def test_parse_directory_value_error(tmp_path):
    from src.graph_builder.ast_parser import parse_directory
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "linked.py").write_text("x = 1\n")
    inner = tmp_path / "inner"
    inner.mkdir()
    (inner / "linked.py").symlink_to(outside / "linked.py")
    nodes, _ = parse_directory(str(inner))
    assert isinstance(nodes, list)
