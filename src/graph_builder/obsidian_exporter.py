"""Export the knowledge graph to Obsidian-compatible vault files.

Produces:
  vault/graph.json   — full node/edge data for programmatic consumption
  vault/graph.html   — interactive vis-network visualization (third Grphify export)
  vault/index.md     — Obsidian index with links to every node note
  vault/hot.md       — Top-N central nodes (hotspots to investigate first)
  vault/nodes/*.md   — One note per code entity with wiki-link relationships

Note rendering logic lives in note_renderer.py.
HTML generation lives in graph_html_writer.py.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.data_types.graph_node import GraphNode, NodeKind
from src.graph_builder.graph_generator import KnowledgeGraph
from src.graph_builder.graph_html_writer import write_graph_html
from src.graph_builder.note_renderer import render_node_note


class ObsidianExporter:
    """Serializes a KnowledgeGraph into an Obsidian vault directory."""

    def __init__(self, vault_dir: str) -> None:
        self.vault = Path(vault_dir)
        self.nodes_dir = self.vault / "nodes"
        self.nodes_dir.mkdir(parents=True, exist_ok=True)

    def export(self, kg: KnowledgeGraph, top_n: int = 15, source_dir: str = "") -> None:
        """Run all export steps: graph.json, graph.html, index.md, hot.md, node notes."""
        payload = self._write_graph_json(kg)
        write_graph_html(self.vault, payload)
        failed_files = self._detect_failed_files(kg, source_dir) if source_dir else []
        self._write_hot(kg, top_n, failed_files)
        self._write_index(kg, failed_files)
        self._write_node_notes(kg, source_dir=source_dir)

    def _write_graph_json(self, kg: KnowledgeGraph) -> dict:
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

        edges_data = [
            {"source": src, "target": tgt,
             "kind": data.get("kind", "Extracted"),
             "label": data.get("label", ""),
             "confidence": data.get("confidence", data.get("weight", 1.0)),
             "source_file": data.get("source_file", "")}
            for src, tgt, data in kg.graph.edges(data=True)
        ]
        m = kg.metrics
        payload = {
            "meta": {"node_count": m.node_count, "edge_count": m.edge_count,
                     "community_count": len(m.communities), "bridge_count": len(m.bridges)},
            "nodes": nodes_data,
            "edges": edges_data,
        }
        (self.vault / "graph.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    def _detect_failed_files(self, kg: KnowledgeGraph, source_dir: str) -> list[str]:
        """Return relative paths of .py files that produced no graph nodes (parse failed)."""
        from pathlib import Path as _Path
        src = _Path(source_dir).resolve()
        # node file_path may be relative (to source_dir) or absolute — normalise both to absolute
        node_files: set[_Path] = set()
        for n in kg._nodes.values():
            fp = _Path(n.file_path)
            node_files.add((src / fp).resolve() if not fp.is_absolute() else fp.resolve())
        failed = []
        for py in sorted(src.rglob("*.py")):
            if py.resolve() not in node_files:
                failed.append(str(py.relative_to(src)))
        return failed

    def _write_hot(self, kg: KnowledgeGraph, top_n: int, failed_files: list[str] | None = None) -> None:
        if failed_files is None:
            failed_files = []
        lines = ["# hot.md — Architectural Hotspots\n"]
        m = kg.metrics

        # If files failed to parse, they are the PRIMARY investigation hotspots.
        if failed_files:
            lines += [
                "> **Sparse graph detected** (`edge_count = 0`). The files below **failed AST parsing** —",
                "> they are the actual investigation hotspots. The centrality table only shows parseable step-files.\n",
                "## ⚠️ Primary Hotspots — Failed AST Parse (Start Here)\n",
                "| Priority | File | Signal | Status |",
                "|---|---|---|---|",
            ]
            for i, fpath in enumerate(failed_files, 1):
                lines.append(f"| 🔴 {i} | `{fpath}` | 0 nodes extracted — syntax errors block AST | **Investigate first** |")
            lines.append("")

        lines += [
            "## Centrality Table (Parseable Nodes Only)\n",
            "Nodes ranked by betweenness centrality (higher = more central = higher risk).\n",
            "| Rank | Node | Kind | Betweenness | In | Out |",
            "|------|------|------|-------------|-----|-----|",
        ]
        for rank, (nid, score) in enumerate(m.top_hubs[:top_n], 1):
            node = kg.get_node(nid)
            name = node.label if node else nid.split("::")[-1]
            kind = node.kind.value if node else "?"
            slug = node.obsidian_slug if node else nid
            lines.append(
                f"| {rank} | [[{slug}\\|{name}]] | {kind} "
                f"| {score:.4f} | {m.in_degree.get(nid, 0)} | {m.out_degree.get(nid, 0)} |"
            )

        if failed_files and all(score == 0 for _, score in m.top_hubs[:top_n]):
            lines += [
                "",
                "> All betweenness = 0.0 because 0 edges exist.",
                "> A healthy codebase of this size would show 5–50 edges.",
                "> Universal zero = broken codebase, not a quiet one.",
            ]

        (self.vault / "hot.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_index(self, kg: KnowledgeGraph, failed_files: list[str] | None = None) -> None:
        if failed_files is None:
            failed_files = []
        by_kind: dict[str, list[GraphNode]] = {}
        for node in kg._nodes.values():
            by_kind.setdefault(node.kind.value, []).append(node)

        lines = ["# index.md — Knowledge Graph Index\n",
                 "Central navigation page for the knowledge vault.\n"]

        if failed_files:
            lines += [
                "## ⚠️ Files That Failed AST Parse (Primary Investigation Targets)\n",
                "These files produced **0 nodes** — they are the actual buggy files.\n",
                "| File | Nodes | Reason |",
                "|---|---|---|",
            ]
            for fpath in failed_files:
                lines.append(f"| `{fpath}` | 0 | Syntax errors blocked AST parsing |")
            lines.append("\n---\n")

        lines.append("## Parseable Entities\n")
        for kind in [NodeKind.CLASS, NodeKind.FUNCTION, NodeKind.METHOD, NodeKind.MODULE, NodeKind.FILE]:
            bucket = by_kind.get(kind.value, [])
            if not bucket:
                continue
            lines.append(f"\n### {kind.value.title()}s ({len(bucket)})\n")
            for node in sorted(bucket, key=lambda n: n.name):
                lines.append(f"- [[{node.obsidian_slug}|{node.label}]] — `{node.file_path}`")
        (self.vault / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_node_notes(self, kg: KnowledgeGraph, source_dir: str = "") -> None:
        for node_id, node in kg._nodes.items():
            note = render_node_note(node_id, node, kg, source_dir=source_dir)
            (self.nodes_dir / f"{node.obsidian_slug}.md").write_text(note, encoding="utf-8")
