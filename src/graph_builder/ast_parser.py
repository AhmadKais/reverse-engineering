"""AST-based Python code parser — extracts nodes and edges from source files.

Implements the 'Extracted' edge layer from Grphify's three-tier taxonomy:
direct imports, function calls, and inheritance are all hard-coded facts
read from the syntax tree, not inferred by a language model.

AST visitor internals live in ast_visitors.py; this module exposes only the
two public functions: parse_file and parse_directory.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

from src.data_types.graph_edge import EdgeKind, EdgeLabel, GraphEdge
from src.data_types.graph_node import GraphNode, NodeKind
from src.graph_builder.ast_visitors import _FileVisitor, _module_id


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

    for _alias_name, fq_name in visitor._imports.items():
        visitor.edges.append(GraphEdge(
            source=_module_id(file_path),
            target=fq_name,
            kind=EdgeKind.EXTRACTED,
            label=EdgeLabel.IMPORTS,
        ))

    return visitor.nodes, visitor.edges


def parse_directory(
    root_path: str, extensions: tuple[str, ...] = (".py",)
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Recursively parse all Python files under root_path."""
    all_nodes: list[GraphNode] = []
    all_edges: list[GraphEdge] = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith((".", "__pycache__", ".venv", "node_modules"))
        ]
        for fname in filenames:
            if any(fname.endswith(ext) for ext in extensions):
                full_path = os.path.join(dirpath, fname)
                nodes, edges = parse_file(full_path)
                all_nodes.extend(nodes)
                all_edges.extend(edges)

    return all_nodes, all_edges
