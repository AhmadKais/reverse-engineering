"""Infer composition edges from constructor calls in a KnowledgeGraph."""

from __future__ import annotations

import networkx as nx

from src.data_types.graph_edge import EdgeKind, EdgeLabel
from src.data_types.graph_node import GraphNode, NodeKind


def infer_composition_edges(
    graph: nx.DiGraph,
    nodes: dict[str, GraphNode],
    name_index: dict[str, list[str]],
) -> None:
    """Add Inferred/COMPOSES edges based on __init__ constructor calls."""
    for node_id, node in nodes.items():
        if node.kind != NodeKind.CLASS:
            continue
        for method_name in node.methods:
            if method_name != "__init__":
                continue
            method_id = f"{node.file_path}::{node.name}.__init__"
            method_node = nodes.get(method_id)
            if not method_node:
                continue
            for callee in method_node.calls:
                targets = name_index.get(callee, [])
                for t in targets:
                    if t != node_id and not graph.has_edge(node_id, t):
                        graph.add_edge(
                            node_id,
                            t,
                            kind=EdgeKind.INFERRED.value,
                            label=EdgeLabel.COMPOSES.value,
                            weight=0.7,
                            confidence=0.7,
                            source_file="",
                        )
