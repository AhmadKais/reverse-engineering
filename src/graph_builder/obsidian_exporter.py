"""Export the knowledge graph to Obsidian-compatible vault files.

Produces:
  vault/graph.json   — full node/edge data for programmatic consumption
  vault/index.md     — Obsidian index with links to every node note
  vault/hot.md       — Top-N central nodes (hotspots to investigate first)
  vault/nodes/*.md   — One note per code entity with wiki-link relationships
"""

from __future__ import annotations

import json
from pathlib import Path

from src.data_types.graph_edge import EdgeKind
from src.data_types.graph_node import GraphNode
from src.graph_builder.graph_generator import KnowledgeGraph


class ObsidianExporter:
    """Serializes a KnowledgeGraph into an Obsidian vault directory."""

    def __init__(self, vault_dir: str) -> None:
        self.vault = Path(vault_dir)
        self.nodes_dir = self.vault / "nodes"
        self.nodes_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------

    def export(self, kg: KnowledgeGraph, top_n: int = 15) -> None:
        """Run all export steps: graph.json, index.md, hot.md, node notes."""
        self._write_graph_json(kg)
        self._write_hot(kg, top_n)
        self._write_index(kg)
        self._write_node_notes(kg)

    # ------------------------------------------------------------------

    def _write_graph_json(self, kg: KnowledgeGraph) -> None:
        """Write the full graph as a structured JSON file."""
        nodes_data = []
        for node_id, data in kg.graph.nodes(data=True):
            node_obj = kg.get_node(node_id)
            entry = {
                "id": node_id,
                "label": data.get("label", node_id),
                "kind": data.get("kind", "unknown"),
                "file": data.get("file", ""),
                "betweenness": round(kg.metrics.betweenness.get(node_id, 0), 5),
                "in_degree": kg.metrics.in_degree.get(node_id, 0),
                "out_degree": kg.metrics.out_degree.get(node_id, 0),
            }
            if node_obj:
                entry["line_start"] = node_obj.line_start
                entry["line_end"] = node_obj.line_end
                entry["docstring"] = node_obj.docstring
            nodes_data.append(entry)

        edges_data = []
        for src, tgt, data in kg.graph.edges(data=True):
            edges_data.append({
                "source": src,
                "target": tgt,
                "kind": data.get("kind", "Extracted"),
                "label": data.get("label", ""),
                "weight": data.get("weight", 1.0),
            })

        m = kg.metrics
        payload = {
            "meta": {
                "node_count": m.node_count,
                "edge_count": m.edge_count,
                "community_count": len(m.communities),
                "bridge_count": len(m.bridges),
            },
            "nodes": nodes_data,
            "edges": edges_data,
        }
        (self.vault / "graph.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _write_hot(self, kg: KnowledgeGraph, top_n: int) -> None:
        """Write hot.md — the top-N most central nodes (architectural hotspots)."""
        lines = [
            "# hot.md — Architectural Hotspots\n",
            "Nodes ranked by betweenness centrality (higher = more central = higher risk).\n",
            "| Rank | Node | Kind | Betweenness | In | Out |",
            "|------|------|------|-------------|-----|-----|",
        ]
        m = kg.metrics
        for rank, (nid, score) in enumerate(m.top_hubs[:top_n], 1):
            node = kg.get_node(nid)
            name = node.label if node else nid.split("::")[-1]
            kind = node.kind.value if node else "?"
            slug = node.obsidian_slug if node else nid
            lines.append(
                f"| {rank} | [[{slug}\\|{name}]] | {kind} "
                f"| {score:.4f} | {m.in_degree.get(nid, 0)} | {m.out_degree.get(nid, 0)} |"
            )
        (self.vault / "hot.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_index(self, kg: KnowledgeGraph) -> None:
        """Write index.md — complete list of all nodes organized by kind."""
        from src.data_types.graph_node import NodeKind

        by_kind: dict[str, list[GraphNode]] = {}
        for node in kg._nodes.values():
            by_kind.setdefault(node.kind.value, []).append(node)

        lines = ["# index.md — Knowledge Graph Index\n"]
        for kind in [NodeKind.CLASS, NodeKind.FUNCTION, NodeKind.METHOD, NodeKind.MODULE, NodeKind.FILE]:
            bucket = by_kind.get(kind.value, [])
            if not bucket:
                continue
            lines.append(f"\n## {kind.value.title()}s ({len(bucket)})\n")
            for node in sorted(bucket, key=lambda n: n.name):
                lines.append(f"- [[{node.obsidian_slug}|{node.label}]] — `{node.file_path}`")

        (self.vault / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_node_notes(self, kg: KnowledgeGraph) -> None:
        """Write one Obsidian note per node with relationship wiki-links."""
        for node_id, node in kg._nodes.items():
            note = self._render_note(node_id, node, kg)
            (self.nodes_dir / f"{node.obsidian_slug}.md").write_text(note, encoding="utf-8")

    def _render_note(self, node_id: str, node: GraphNode, kg: KnowledgeGraph) -> str:
        """Render a single node as an Obsidian markdown note."""
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

        # Outgoing edges
        out_edges = [(tgt, data) for _, tgt, data in kg.graph.out_edges(node_id, data=True)]
        if out_edges:
            lines += ["## Outgoing Relationships", ""]
            for tgt, data in out_edges:
                tgt_node = kg.get_node(tgt)
                tgt_label = tgt_node.label if tgt_node else tgt.split("::")[-1]
                tgt_slug = tgt_node.obsidian_slug if tgt_node else tgt
                edge_kind = data.get("kind", "?")
                edge_lbl = data.get("label", "?")
                lines.append(f"- [[{tgt_slug}|{tgt_label}]] `{edge_kind}:{edge_lbl}`")
            lines.append("")

        # Incoming edges
        in_edges = [(src, data) for src, _, data in kg.graph.in_edges(node_id, data=True)]
        if in_edges:
            lines += ["## Incoming Relationships", ""]
            for src, data in in_edges:
                src_node = kg.get_node(src)
                src_label = src_node.label if src_node else src.split("::")[-1]
                src_slug = src_node.obsidian_slug if src_node else src
                edge_kind = data.get("kind", "?")
                edge_lbl = data.get("label", "?")
                lines.append(f"- [[{src_slug}|{src_label}]] `{edge_kind}:{edge_lbl}`")
            lines.append("")

        return "\n".join(lines)
