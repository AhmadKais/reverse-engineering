"""AST-based Python code parser — extracts nodes and edges from source files.

Implements the 'Extracted' edge layer from Grphify's three-tier taxonomy:
direct imports, function calls, and inheritance are all hard-coded facts
read from the syntax tree, not inferred by a language model.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

from src.data_types.graph_edge import EdgeKind, EdgeLabel, GraphEdge
from src.data_types.graph_node import GraphNode, NodeKind


def _node_id(file_path: str, name: str, parent: str | None = None) -> str:
    """Build a deterministic, collision-free node ID from path + name."""
    rel = file_path.replace(os.sep, "/")
    if parent:
        return f"{rel}::{parent}.{name}"
    return f"{rel}::{name}"


def _module_id(file_path: str) -> str:
    return file_path.replace(os.sep, "/") + "::__module__"


class _FileVisitor(ast.NodeVisitor):
    """Single-file AST visitor: extracts classes, methods, functions, and imports."""

    def __init__(self, file_path: str, source_lines: list[str]) -> None:
        self.file_path = file_path
        self.source_lines = source_lines
        self.nodes: list[GraphNode] = []
        self.edges: list[GraphEdge] = []
        self._current_class: str | None = None
        self._imports: dict[str, str] = {}   # alias → fully-qualified name

    # ------------------------------------------------------------------ imports

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            key = alias.asname or alias.name.split(".")[0]
            self._imports[key] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            key = alias.asname or alias.name
            self._imports[key] = f"{module}.{alias.name}"
        self.generic_visit(node)

    # ------------------------------------------------------------------ classes

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
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
        # Inheritance edges (Extracted)
        for base in base_names:
            self.edges.append(GraphEdge(
                source=class_id,
                target=base,    # resolved later against full node list
                kind=EdgeKind.EXTRACTED,
                label=EdgeLabel.INHERITS,
            ))
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = None

    def _base_name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return self._imports.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            return f"{self._base_name(node.value)}.{node.attr}"
        return "object"

    # ------------------------------------------------------------------ functions / methods

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
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
        # Call edges (Extracted) — resolved post-parse against the full graph
        for callee in calls:
            self.edges.append(GraphEdge(
                source=fn_id,
                target=callee,
                kind=EdgeKind.EXTRACTED,
                label=EdgeLabel.CALLS,
            ))
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def _collect_calls(self, fn_node: ast.AST) -> list[str]:
        """Return list of called names (Name or Attribute.attr) inside fn_node."""
        calls: list[str] = []
        for node in ast.walk(fn_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)
        return list(dict.fromkeys(calls))   # deduplicate, preserve order


def parse_file(file_path: str) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Parse one Python source file; return its nodes and raw (unresolved) edges."""
    try:
        source = Path(file_path).read_text(encoding="utf-8")
    except OSError:
        return [], []
    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError:
        return [], []

    lines = source.splitlines()
    visitor = _FileVisitor(file_path, lines)

    # Module-level node
    module_node = GraphNode(
        id=_module_id(file_path),
        kind=NodeKind.MODULE,
        name=Path(file_path).stem,
        file_path=file_path,
        line_start=1,
        line_end=len(lines),
        docstring=(ast.get_docstring(tree) or "")[:200],
    )
    visitor.nodes.append(module_node)
    visitor.visit(tree)

    # Module imports edges (Extracted)
    for alias_name, fq_name in visitor._imports.items():
        visitor.edges.append(GraphEdge(
            source=_module_id(file_path),
            target=fq_name,
            kind=EdgeKind.EXTRACTED,
            label=EdgeLabel.IMPORTS,
        ))

    return visitor.nodes, visitor.edges


def parse_directory(root_path: str, extensions: tuple[str, ...] = (".py",)) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Recursively parse all Python files under root_path."""
    all_nodes: list[GraphNode] = []
    all_edges: list[GraphEdge] = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if not d.startswith((".", "__pycache__", ".venv", "node_modules"))]
        for fname in filenames:
            if any(fname.endswith(ext) for ext in extensions):
                full_path = os.path.join(dirpath, fname)
                nodes, edges = parse_file(full_path)
                all_nodes.extend(nodes)
                all_edges.extend(edges)

    return all_nodes, all_edges
