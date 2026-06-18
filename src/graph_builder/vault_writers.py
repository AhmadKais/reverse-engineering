"""Standalone markdown writers for Obsidian vault pages (hot.md and index.md)."""

from __future__ import annotations

from pathlib import Path

from src.data_types.graph_node import GraphNode, NodeKind
from src.graph_builder.graph_generator import KnowledgeGraph


def write_hot(vault: Path, kg: KnowledgeGraph, top_n: int,
              failed_files: list[str] | None = None) -> None:
    """Write hot.md — ranked hotspot table with betweenness centrality scores."""
    if failed_files is None:
        failed_files = []
    lines = ["# hot.md — Architectural Hotspots\n"]
    m = kg.metrics

    if failed_files:
        lines += [
            "> **Sparse graph detected** (`edge_count = 0`). The files below **failed AST parsing** —",
            "> they are the actual investigation hotspots. The centrality table only shows parseable step-files.\n",
            "## ⚠️ Primary Hotspots — Failed AST Parse (Start Here)\n",
            "| Priority | File | Signal | Status |",
            "|---|---|---|---|",
        ]
        for i, fpath in enumerate(failed_files, 1):
            lines.append(
                f"| 🔴 {i} | `{fpath}` | 0 nodes extracted — syntax errors block AST | **Investigate first** |"
            )
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

    (vault / "hot.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_index(vault: Path, kg: KnowledgeGraph, failed_files: list[str] | None = None) -> None:
    """Write index.md — full entity index with wiki-links to every node note."""
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
    (vault / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
