"""Targeted tests to cover specific previously-uncovered code paths."""

from __future__ import annotations

from unittest.mock import patch

from src.data_types.graph_edge import EdgeKind, EdgeLabel, GraphEdge
from src.data_types.graph_node import GraphNode, NodeKind
from src.graph_builder.graph_generator import KnowledgeGraph
from src.graph_builder.vault_writers import write_hot, write_index

# ---------------------------------------------------------------------------
# version.py
# ---------------------------------------------------------------------------

def test_version_importable():
    from src.version import PROJECT_NAME, VERSION
    assert VERSION == "1.00"
    assert PROJECT_NAME == "reverse-engineer-agent"


# ---------------------------------------------------------------------------
# langgraph_workflow — print_workflow_diagram
# ---------------------------------------------------------------------------

def test_print_workflow_diagram(capsys):
    from src.langgraph_workflow import print_workflow_diagram
    print_workflow_diagram()
    captured = capsys.readouterr()
    assert "build_graph" in captured.out


# ---------------------------------------------------------------------------
# graph_generator — metrics cached branch (line 108)
# ---------------------------------------------------------------------------

def test_metrics_cached_second_call():
    kg = KnowledgeGraph()
    kg.build([], [])
    m1 = kg.metrics
    m2 = kg.metrics          # second access hits the cached branch
    assert m1 is m2


# ---------------------------------------------------------------------------
# graph_generator — _resolve_target where target IS a known node ID (line 65)
# ---------------------------------------------------------------------------

def test_resolve_target_exact_id_match():
    node = GraphNode(id="foo.py::MyClass", kind=NodeKind.CLASS, name="MyClass",
                     file_path="foo.py", line_start=1, line_end=10)
    edge = GraphEdge(source="foo.py::MyClass", target="foo.py::MyClass",
                     kind=EdgeKind.EXTRACTED, label=EdgeLabel.CALLS, confidence=1.0)
    kg = KnowledgeGraph()
    kg.build([node], [edge])   # edge target == node id → hits line 65
    assert kg.graph.number_of_nodes() == 1


# ---------------------------------------------------------------------------
# graph_generator — bridge exception (lines 89-90: mocked NetworkXError)
# ---------------------------------------------------------------------------

def test_compute_metrics_bridge_exception():
    import networkx as nx
    kg = KnowledgeGraph()
    kg.build([], [])
    with patch.object(nx, "bridges", side_effect=nx.NetworkXError("self-loop")):
        kg._metrics = None
        m = kg.compute_metrics()
    assert m.bridges == []


# ---------------------------------------------------------------------------
# graph_generator — community exception (lines 90-91)
# ---------------------------------------------------------------------------

def test_compute_metrics_community_exception():
    kg = KnowledgeGraph()
    kg.build([], [])
    with patch("networkx.community.greedy_modularity_communities",
               side_effect=Exception("forced")):
        kg._metrics = None
        m = kg.compute_metrics()
    assert m.communities == []


# ---------------------------------------------------------------------------
# edge_inferrer — full composition path (lines 27-31) + missing method (line 26)
# ---------------------------------------------------------------------------

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
    # Class with __init__ in methods list but no corresponding method node → hits line 26
    orphan = GraphNode(id="x.py::Orphan", kind=NodeKind.CLASS, name="Orphan",
                       file_path="x.py", line_start=1, line_end=5,
                       methods=["__init__"])
    kg = KnowledgeGraph()
    kg.build([orphan], [])
    assert kg.graph.number_of_nodes() == 1


# ---------------------------------------------------------------------------
# ast_visitors — attribute base (existing) + unknown base → "object" (line 92)
# ---------------------------------------------------------------------------

def test_ast_visitors_attribute_base_name(tmp_path):
    from src.graph_builder.ast_parser import parse_file
    code = "class Child(base.Parent):\n    pass\n"
    src = tmp_path / "child.py"
    src.write_text(code)
    nodes, edges = parse_file(str(src))
    kinds = {n.name for n in nodes}
    assert "Child" in kinds


def test_ast_visitors_unknown_base_name(tmp_path):
    from src.graph_builder.ast_parser import parse_file
    # list[int] parses to ast.Subscript — not Name or Attribute → returns "object"
    code = "class Foo(list[int]):\n    pass\n"
    src = tmp_path / "subscript_base.py"
    src.write_text(code)
    nodes, edges = parse_file(str(src))
    kinds = {n.name for n in nodes}
    assert "Foo" in kinds


# ---------------------------------------------------------------------------
# ast_parser — OSError on unreadable file (lines 35-36)
# ---------------------------------------------------------------------------

def test_parse_file_oserror():
    from src.graph_builder.ast_parser import parse_file
    nodes, edges = parse_file("/nonexistent/path/that/cannot/exist.py")
    assert nodes == [] and edges == []


# ---------------------------------------------------------------------------
# ast_parser — ValueError in parse_directory (lines 90-91: symlink outside root)
# ---------------------------------------------------------------------------

def test_parse_directory_value_error(tmp_path):
    from src.graph_builder.ast_parser import parse_directory
    # Symlink inside inner/ that resolves to outside/, triggering ValueError
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "linked.py").write_text("x = 1\n")
    inner = tmp_path / "inner"
    inner.mkdir()
    (inner / "linked.py").symlink_to(outside / "linked.py")
    nodes, edges = parse_directory(str(inner))
    assert isinstance(nodes, list)


# ---------------------------------------------------------------------------
# note_renderer — snippet truncation + suppress fallback (line 26 = return "")
# ---------------------------------------------------------------------------

def test_note_renderer_long_source(tmp_path):
    from src.graph_builder.note_renderer import render_node_note
    long_code = "\n".join(f"line_{i} = {i}" for i in range(40))
    src = tmp_path / "big.py"
    src.write_text(long_code)
    node = GraphNode(id="big.py::__module__", kind=NodeKind.MODULE, name="big",
                     file_path="big.py", line_start=1, line_end=40,
                     docstring="x" * 250)
    kg = KnowledgeGraph()
    kg.build([node], [])
    note = render_node_note("big.py::__module__", node, kg, source_dir=str(tmp_path))
    assert "truncated" in note
    assert "x" * 50 in note


def test_read_snippet_suppress_fallback():
    from src.graph_builder.note_renderer import _read_snippet
    # Nonexistent file → FileNotFoundError suppressed → return "" (line 26)
    node = GraphNode(id="x.py::f", kind=NodeKind.FUNCTION, name="f",
                     file_path="nonexistent_xyz987.py", line_start=1, line_end=5)
    result = _read_snippet(node, "/tmp/bogus_source_dir_xyz")
    assert result == ""


# ---------------------------------------------------------------------------
# vault_writers — None → [] default (lines 14, 61)
# ---------------------------------------------------------------------------

def test_write_hot_none_failed_files(tmp_path):
    kg = KnowledgeGraph()
    kg.build([], [])
    write_hot(tmp_path, kg, top_n=5, failed_files=None)  # triggers line 14
    assert (tmp_path / "hot.md").exists()


def test_write_index_none_failed_files(tmp_path):
    kg = KnowledgeGraph()
    kg.build([], [])
    write_index(tmp_path, kg, failed_files=None)  # triggers line 61
    assert (tmp_path / "index.md").exists()
