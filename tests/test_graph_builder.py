"""Unit tests for the AST parser and graph generator."""

from __future__ import annotations

import textwrap
import tempfile
import os
from pathlib import Path

import pytest

from src.graph_builder.ast_parser import parse_file, parse_directory
from src.graph_builder.graph_generator import KnowledgeGraph
from src.data_types.graph_node import NodeKind
from src.data_types.graph_edge import EdgeKind, EdgeLabel


# ------------------------------------------------------------------ helpers

def write_temp_py(content: str, filename: str = "test_module.py") -> str:
    """Write a Python source string to a temp file and return its path."""
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, filename)
    Path(path).write_text(textwrap.dedent(content), encoding="utf-8")
    return path


# ------------------------------------------------------------------ parse_file tests

class TestASTParser:
    def test_parses_module_node(self):
        path = write_temp_py('"""A module."""\n')
        nodes, _ = parse_file(path)
        module_nodes = [n for n in nodes if n.kind == NodeKind.MODULE]
        assert len(module_nodes) == 1
        assert module_nodes[0].docstring == "A module."

    def test_parses_class(self):
        path = write_temp_py("""
            class Foo:
                pass
        """)
        nodes, _ = parse_file(path)
        class_nodes = [n for n in nodes if n.kind == NodeKind.CLASS]
        assert any(n.name == "Foo" for n in class_nodes)

    def test_parses_class_with_inheritance(self):
        path = write_temp_py("""
            class Base:
                pass

            class Child(Base):
                pass
        """)
        nodes, edges = parse_file(path)
        inherit_edges = [e for e in edges if e.label == EdgeLabel.INHERITS]
        assert len(inherit_edges) >= 1
        child = next(n for n in nodes if n.name == "Child")
        assert "Base" in child.base_classes

    def test_parses_function(self):
        path = write_temp_py("""
            def greet(name: str) -> str:
                return f"hello {name}"
        """)
        nodes, _ = parse_file(path)
        fn_nodes = [n for n in nodes if n.kind == NodeKind.FUNCTION]
        assert any(n.name == "greet" for n in fn_nodes)

    def test_parses_method(self):
        path = write_temp_py("""
            class Agent:
                def run(self):
                    pass
        """)
        nodes, _ = parse_file(path)
        method_nodes = [n for n in nodes if n.kind == NodeKind.METHOD]
        assert any(n.name == "run" for n in method_nodes)

    def test_parses_imports(self):
        path = write_temp_py("""
            import os
            from pathlib import Path
        """)
        nodes, edges = parse_file(path)
        import_edges = [e for e in edges if e.label == EdgeLabel.IMPORTS]
        assert len(import_edges) >= 2

    def test_handles_syntax_error_gracefully(self):
        path = write_temp_py("def broken(\n  # unclosed")
        nodes, edges = parse_file(path)
        assert nodes == []
        assert edges == []

    def test_detects_function_calls(self):
        path = write_temp_py("""
            def caller():
                result = helper()
                return result

            def helper():
                return 42
        """)
        nodes, edges = parse_file(path)
        call_edges = [e for e in edges if e.label == EdgeLabel.CALLS]
        assert any(e.target == "helper" for e in call_edges)

    def test_line_numbers_recorded(self):
        path = write_temp_py("""
            class MyClass:
                def my_method(self):
                    pass
        """)
        nodes, _ = parse_file(path)
        cls_node = next((n for n in nodes if n.name == "MyClass"), None)
        assert cls_node is not None
        assert cls_node.line_start >= 1
        assert cls_node.line_end >= cls_node.line_start

    def test_parse_directory_finds_all_files(self):
        tmpdir = tempfile.mkdtemp()
        for name in ["a.py", "b.py"]:
            Path(os.path.join(tmpdir, name)).write_text("x = 1\n", encoding="utf-8")
        Path(os.path.join(tmpdir, "__pycache__")).mkdir()
        Path(os.path.join(tmpdir, "__pycache__", "cached.py")).write_text("# cache\n", encoding="utf-8")
        nodes, _ = parse_directory(tmpdir)
        file_paths = {n.file_path for n in nodes}
        assert not any("__pycache__" in p for p in file_paths), "Should skip __pycache__"
        assert any("a.py" in p for p in file_paths)
        assert any("b.py" in p for p in file_paths)


# ------------------------------------------------------------------ KnowledgeGraph tests

class TestKnowledgeGraph:
    def _make_kg_from_source(self, source: str) -> KnowledgeGraph:
        path = write_temp_py(source)
        nodes, edges = parse_file(path)
        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        return kg

    def test_graph_has_nodes(self):
        kg = self._make_kg_from_source("""
            class A:
                pass
            class B(A):
                pass
        """)
        assert kg.graph.number_of_nodes() > 0

    def test_computes_metrics(self):
        kg = self._make_kg_from_source("""
            class Hub:
                def method_a(self): pass
                def method_b(self): pass
            class Worker(Hub):
                pass
        """)
        m = kg.compute_metrics()
        assert m.node_count > 0
        assert isinstance(m.betweenness, dict)
        assert isinstance(m.top_hubs, list)

    def test_top_hubs_are_sorted_descending(self):
        kg = self._make_kg_from_source("""
            class A:
                pass
            class B(A):
                pass
            class C(B):
                pass
        """)
        m = kg.compute_metrics()
        scores = [score for _, score in m.top_hubs]
        assert scores == sorted(scores, reverse=True)

    def test_summary_dict_is_serializable(self):
        import json
        kg = self._make_kg_from_source("class X:\n    pass\n")
        kg.compute_metrics()
        summary = kg.summary_dict()
        # Must be JSON-serializable
        assert json.dumps(summary)

    def test_community_detection_runs(self):
        kg = self._make_kg_from_source("""
            class A:
                pass
            class B(A):
                pass
            class C:
                pass
        """)
        m = kg.compute_metrics()
        assert isinstance(m.communities, list)

    def test_get_node_returns_none_for_unknown(self):
        kg = self._make_kg_from_source("x = 1\n")
        assert kg.get_node("nonexistent::id") is None

    def test_build_with_real_broken_python(self):
        """Integration smoke test: parse broken-python source (no API calls)."""
        broken_src = Path(__file__).parent.parent / "data" / "broken-python"
        if not broken_src.exists():
            pytest.skip("broken-python source not found")
        nodes, edges = parse_directory(str(broken_src))
        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        m = kg.compute_metrics()
        assert m.node_count >= 5, "broken-python should have at least 5 nodes"
