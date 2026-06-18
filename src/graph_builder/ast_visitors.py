"""AST visitor and node-ID helpers — extracted from ast_parser for file-size compliance."""

from __future__ import annotations

import ast
import os

from src.data_types.graph_edge import EdgeKind, EdgeLabel, GraphEdge
from src.data_types.graph_node import GraphNode, NodeKind


def _node_id(file_path: str, name: str, parent: str | None = None) -> str:
    """Build a deterministic, collision-free node ID from path + name."""
    rel = file_path.replace(os.sep, "/")
    if parent:
        return f"{rel}::{parent}.{name}"
    return f"{rel}::{name}"


def _module_id(file_path: str) -> str:
    """Build the canonical module-level node ID for a given file path."""
    return file_path.replace(os.sep, "/") + "::__module__"


class _FileVisitor(ast.NodeVisitor):
    """Single-file AST visitor: extracts classes, methods, functions, and imports."""

    def __init__(self, file_path: str, source_lines: list[str]) -> None:
        """Initialise visitor state for a single source file."""
        self.file_path = file_path
        self.source_lines = source_lines
        self.nodes: list[GraphNode] = []
        self.edges: list[GraphEdge] = []
        self._current_class: str | None = None
        self._imports: dict[str, str] = {}

    def visit_Import(self, node: ast.Import) -> None:
        """Record `import X` and `import X as Y` statements in the import map."""
        for alias in node.names:
            key = alias.asname or alias.name.split(".")[0]
            self._imports[key] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Record `from X import Y` statements in the import map."""
        module = node.module or ""
        for alias in node.names:
            key = alias.asname or alias.name
            self._imports[key] = f"{module}.{alias.name}"
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Extract class node and inheritance edges; descend into methods."""
        class_id = _node_id(self.file_path, node.name)
        base_names = [self._base_name(b) for b in node.bases]
        docstring = ast.get_docstring(node) or ""
        method_names: list[str] = [
            n.name for n in ast.walk(node)
            if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)
            and n.col_offset == node.col_offset + 4
        ]
        self.nodes.append(GraphNode(
            id=class_id,
            kind=NodeKind.CLASS,
            name=node.name,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=docstring[:200],
            base_classes=base_names,
            methods=method_names,
        ))
        for base in base_names:
            self.edges.append(GraphEdge(
                source=class_id,
                target=base,
                kind=EdgeKind.EXTRACTED,
                label=EdgeLabel.INHERITS,
                confidence=1.0,
                source_file=self.file_path,
            ))
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = None

    def _base_name(self, node: ast.expr) -> str:
        """Resolve a base-class AST node to a dotted name string."""
        if isinstance(node, ast.Name):
            return self._imports.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            return f"{self._base_name(node.value)}.{node.attr}"
        return "object"

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Extract a function or method node and its outgoing call edges."""
        kind = NodeKind.METHOD if self._current_class else NodeKind.FUNCTION
        fn_id = _node_id(self.file_path, node.name, self._current_class)
        docstring = ast.get_docstring(node) or ""
        calls = self._collect_calls(node)
        self.nodes.append(GraphNode(
            id=fn_id,
            kind=kind,
            name=node.name,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=docstring[:200],
            parent_class=self._current_class,
            calls=calls,
        ))
        for callee in calls:
            self.edges.append(GraphEdge(
                source=fn_id,
                target=callee,
                kind=EdgeKind.EXTRACTED,
                label=EdgeLabel.CALLS,
                confidence=1.0,
                source_file=self.file_path,
            ))
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef  # noqa: N815

    def _collect_calls(self, fn_node: ast.AST) -> list[str]:
        """Return deduplicated list of called names inside fn_node."""
        calls: list[str] = []
        for node in ast.walk(fn_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)
        return list(dict.fromkeys(calls))
