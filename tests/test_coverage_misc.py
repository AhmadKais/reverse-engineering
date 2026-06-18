"""Targeted tests for version, workflow diagram, note_renderer, and vault_writers."""

from __future__ import annotations

from src.data_types.graph_node import GraphNode, NodeKind
from src.graph_builder.graph_generator import KnowledgeGraph
from src.graph_builder.vault_writers import write_hot, write_index


def test_version_importable():
    from src.version import PROJECT_NAME, VERSION
    assert VERSION == "1.00"
    assert PROJECT_NAME == "reverse-engineer-agent"


def test_print_workflow_diagram(capsys):
    from src.langgraph_workflow import print_workflow_diagram
    print_workflow_diagram()
    captured = capsys.readouterr()
    assert "build_graph" in captured.out


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
    node = GraphNode(id="x.py::f", kind=NodeKind.FUNCTION, name="f",
                     file_path="nonexistent_xyz987.py", line_start=1, line_end=5)
    result = _read_snippet(node, "/tmp/bogus_source_dir_xyz")
    assert result == ""


def test_write_hot_none_failed_files(tmp_path):
    kg = KnowledgeGraph()
    kg.build([], [])
    write_hot(tmp_path, kg, top_n=5, failed_files=None)
    assert (tmp_path / "hot.md").exists()


def test_write_index_none_failed_files(tmp_path):
    kg = KnowledgeGraph()
    kg.build([], [])
    write_index(tmp_path, kg, failed_files=None)
    assert (tmp_path / "index.md").exists()
