"""Unit tests for the AST parser (parse_file / parse_directory)."""

from __future__ import annotations

import os
import tempfile
import textwrap
from pathlib import Path

from src.data_types.graph_edge import EdgeLabel
from src.data_types.graph_node import NodeKind
from src.graph_builder.ast_parser import parse_directory, parse_file


def write_temp_py(content: str, filename: str = "test_module.py") -> str:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, filename)
    Path(path).write_text(textwrap.dedent(content), encoding="utf-8")
    return path


class TestASTParser:
    def test_parses_module_node(self):
        path = write_temp_py('"""A module."""\n')
        nodes, _ = parse_file(path)
        module_nodes = [n for n in nodes if n.kind == NodeKind.MODULE]
        assert len(module_nodes) == 1
        assert module_nodes[0].docstring == "A module."

    def test_parses_class(self):
        path = write_temp_py("class Foo:\n    pass\n")
        nodes, _ = parse_file(path)
        assert any(n.name == "Foo" and n.kind == NodeKind.CLASS for n in nodes)

    def test_parses_class_with_inheritance(self):
        path = write_temp_py("class Base:\n    pass\nclass Child(Base):\n    pass\n")
        nodes, edges = parse_file(path)
        inherit_edges = [e for e in edges if e.label == EdgeLabel.INHERITS]
        assert len(inherit_edges) >= 1
        child = next(n for n in nodes if n.name == "Child")
        assert "Base" in child.base_classes

    def test_parses_function(self):
        path = write_temp_py('def greet(name: str) -> str:\n    return f"hello {name}"\n')
        nodes, _ = parse_file(path)
        assert any(n.name == "greet" and n.kind == NodeKind.FUNCTION for n in nodes)

    def test_parses_method(self):
        path = write_temp_py("class Agent:\n    def run(self):\n        pass\n")
        nodes, _ = parse_file(path)
        assert any(n.name == "run" and n.kind == NodeKind.METHOD for n in nodes)

    def test_parses_imports(self):
        path = write_temp_py("import os\nfrom pathlib import Path\n")
        _, edges = parse_file(path)
        import_edges = [e for e in edges if e.label == EdgeLabel.IMPORTS]
        assert len(import_edges) >= 2

    def test_handles_syntax_error_gracefully(self):
        path = write_temp_py("def broken(\n  # unclosed")
        nodes, edges = parse_file(path)
        assert nodes == [] and edges == []

    def test_detects_function_calls(self):
        path = write_temp_py(
            "def caller():\n    result = helper()\n    return result\n\ndef helper():\n    return 42\n"
        )
        _, edges = parse_file(path)
        call_edges = [e for e in edges if e.label == EdgeLabel.CALLS]
        assert any(e.target == "helper" for e in call_edges)

    def test_line_numbers_recorded(self):
        path = write_temp_py("class MyClass:\n    def my_method(self):\n        pass\n")
        nodes, _ = parse_file(path)
        cls_node = next((n for n in nodes if n.name == "MyClass"), None)
        assert cls_node is not None
        assert cls_node.line_start >= 1
        assert cls_node.line_end >= cls_node.line_start

    def test_parse_directory_finds_all_files(self):
        tmpdir = tempfile.mkdtemp()
        for name in ["a.py", "b.py"]:
            Path(os.path.join(tmpdir, name)).write_text("x = 1\n", encoding="utf-8")
        pycache = Path(os.path.join(tmpdir, "__pycache__"))
        pycache.mkdir()
        (pycache / "cached.py").write_text("# cache\n", encoding="utf-8")
        nodes, _ = parse_directory(tmpdir)
        file_paths = {n.file_path for n in nodes}
        assert not any("__pycache__" in p for p in file_paths)
        assert any("a.py" in p for p in file_paths)
        assert any("b.py" in p for p in file_paths)
