"""Note renderer — converts a GraphNode into an Obsidian markdown note."""

from __future__ import annotations

from src.data_types.graph_node import GraphNode
from src.graph_builder.graph_generator import KnowledgeGraph


def render_node_note(node_id: str, node: GraphNode, kg: KnowledgeGraph) -> str:
    """Render a single node as an Obsidian markdown note with wiki-link relationships."""
    m = kg.metrics
    lines = [
        f"# {node.label}",
        "",
        f"**Kind**: `{node.kind.value}`  ",
        f"**File**: `{node.file_path}`  ",
        f"**Lines**: {node.line_start}–{node.line_end}  ",
        f"**Betweenness Centrality**: {m.betweenness.get(node_id, 0):.4f}  ",
        f"**In-degree**: {m.in_degree.get(node_id, 0)} | **Out-degree**: {m.out_degree.get(node_id, 0)}",
        "",
    ]
    if node.docstring:
        lines += [f"> {node.docstring[:180]}", ""]

    if node.base_classes:
        lines += ["## Inherits From", ""]
        for base in node.base_classes:
            lines.append(f"- [[{base}]]")
        lines.append("")

    if node.methods:
        lines += ["## Methods", ""]
        for method in node.methods:
            lines.append(f"- `{method}`")
        lines.append("")

    out_edges = [(tgt, data) for _, tgt, data in kg.graph.out_edges(node_id, data=True)]
    if out_edges:
        lines += ["## Outgoing Relationships", ""]
        for tgt, data in out_edges:
            tgt_node = kg.get_node(tgt)
            tgt_label = tgt_node.label if tgt_node else tgt.split("::")[-1]
            tgt_slug = tgt_node.obsidian_slug if tgt_node else tgt
            lines.append(
                f"- [[{tgt_slug}|{tgt_label}]] `{data.get('kind', '?')}:{data.get('label', '?')}`"
            )
        lines.append("")

    in_edges = [(src, data) for src, _, data in kg.graph.in_edges(node_id, data=True)]
    if in_edges:
        lines += ["## Incoming Relationships", ""]
        for src, data in in_edges:
            src_node = kg.get_node(src)
            src_label = src_node.label if src_node else src.split("::")[-1]
            src_slug = src_node.obsidian_slug if src_node else src
            lines.append(
                f"- [[{src_slug}|{src_label}]] `{data.get('kind', '?')}:{data.get('label', '?')}`"
            )
        lines.append("")

    return "\n".join(lines)
