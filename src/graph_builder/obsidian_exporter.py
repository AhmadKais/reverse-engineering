"""Export the knowledge graph to Obsidian-compatible vault files.

Produces:
  vault/graph.json   — full node/edge data for programmatic consumption
  vault/graph.html   — interactive vis-network visualization
  vault/index.md     — Obsidian index with links to every node note
  vault/hot.md       — Top-N central nodes (hotspots to investigate first)
  vault/nodes/*.md   — One note per code entity with wiki-link relationships

Note rendering: note_renderer.py  |  HTML: graph_html_writer.py  |  Pages: vault_writers.py
"""

from __future__ import annotations

import json
from pathlib import Path

from src.graph_builder.graph_generator import KnowledgeGraph
from src.graph_builder.graph_html_writer import write_graph_html
from src.graph_builder.note_renderer import render_node_note
from src.graph_builder.vault_writers import write_hot, write_index


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
        write_hot(self.vault, kg, top_n, failed_files)
        write_index(self.vault, kg, failed_files)
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
        src = Path(source_dir).resolve()
        node_files: set[Path] = set()
        for n in kg._nodes.values():
            fp = Path(n.file_path)
            node_files.add((src / fp).resolve() if not fp.is_absolute() else fp.resolve())
        failed = []
        for py in sorted(src.rglob("*.py")):
            if py.resolve() not in node_files:
                failed.append(str(py.relative_to(src)))
        return failed

    def _write_node_notes(self, kg: KnowledgeGraph, source_dir: str = "") -> None:
        for node_id, node in kg._nodes.items():
            note = render_node_note(node_id, node, kg, source_dir=source_dir)
            (self.nodes_dir / f"{node.obsidian_slug}.md").write_text(note, encoding="utf-8")
