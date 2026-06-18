"""Graph-only and naive baseline runners."""

from __future__ import annotations

from pathlib import Path


def _run_graph_only(source: str, vault_dir: str) -> None:
    from src.graph_builder.ast_parser import parse_directory
    from src.graph_builder.graph_generator import KnowledgeGraph
    from src.graph_builder.obsidian_exporter import ObsidianExporter

    source = str(Path(source).resolve())
    print(f"[graph-only] Parsing: {source}")
    nodes, edges = parse_directory(source)
    kg = KnowledgeGraph()
    kg.build(nodes, edges)
    m = kg.compute_metrics()

    print(f"[graph-only] Nodes: {m.node_count}  Edges: {m.edge_count}")
    print(f"[graph-only] Communities: {len(m.communities)}  Bridges: {len(m.bridges)}")
    print("\nTop 10 Hubs by Betweenness Centrality:")
    for nid, score in m.top_hubs[:10]:
        node = kg.get_node(nid)
        name = node.label if node else nid
        kind = node.kind.value if node else "?"
        print(f"  [{score:.4f}] {name} ({kind})")

    ObsidianExporter(vault_dir).export(kg, source_dir=source)
    print(f"\n[graph-only] Vault exported to: {vault_dir}/")
    print(f"  graph.json, index.md, hot.md, nodes/ ({m.node_count} files)")


def _run_naive(source: str, budget: int) -> None:
    """Naive baseline: send ALL .py files to every agent — no graph routing.

    Contrast with the graph-guided pipeline:
    - No KnowledgeGraph built
    - No Obsidian vault consulted
    - No sparse/dense detection
    - No targeted file selection
    Every file is concatenated and sent in full to Analyzer then Fixer.
    Token counts from this run feed TOKEN_COMPARISON.md.
    """
    from src.agents.analyzer_agent import AnalyzerAgent
    from src.agents.base_agent import AgentBudget
    from src.agents.fixer_agent import FixerAgent

    print(f"[naive] Starting naive baseline on: {source}")
    print(f"[naive] Budget: {budget:,} tokens")
    print("[naive] Mode: ALL files → Analyzer → Fixer (no graph, no Obsidian)\n")

    py_files = sorted(Path(source).rglob("*.py"))
    print(f"[naive] Reading {len(py_files)} Python files:")
    all_blocks: list[str] = []
    total_bytes = 0
    for py_file in py_files:
        try:
            content = py_file.read_text(encoding="utf-8")
            total_bytes += len(content.encode("utf-8"))
            rel = py_file.relative_to(source)
            print(f"  {rel}  ({len(content):,} bytes)")
            all_blocks.append(f"### {rel}\n```python\n{content}\n```")
        except OSError:
            pass
    file_contents = "\n\n".join(all_blocks)
    print(f"\n[naive] Total context: {total_bytes:,} bytes across {len(py_files)} files\n")

    budget_obj = AgentBudget(budget)

    print("[naive] Step 1 — AnalyzerAgent (all files in context, no graph summary)")
    analyzer = AnalyzerAgent(budget_obj)
    bug_report = analyzer.analyze_raw(file_contents)
    bugs = bug_report.get("bugs", [])
    print(f"[naive]   Bugs found: {len(bugs)}")
    after_analyze = budget_obj.total_used
    print(f"[naive]   Tokens after Analyzer: {after_analyze:,}\n")

    print("[naive] Step 2 — FixerAgent (all files in context)")
    fixer = FixerAgent(budget_obj)
    fix_report = fixer.propose_fixes_raw(bug_report, file_contents)
    fixes = fix_report.get("fixes", [])
    print(f"[naive]   Fixes proposed: {len(fixes)}")
    total_used = budget_obj.total_used
    print(f"[naive]   Tokens after Fixer:    {total_used:,}\n")

    print("=" * 60)
    print("NAIVE BASELINE — FINAL REPORT")
    print("=" * 60)
    print(f"Files sent to agents : {len(py_files)} (all .py files, unfiltered)")
    print(f"Total bytes in context: {total_bytes:,}")
    print(f"Bugs found           : {len(bugs)}")
    print(f"Fixes proposed       : {len(fixes)}")
    usage = budget_obj.status()
    print(f"Token usage          : {usage['total_used']:,} / {budget:,} "
          f"({100 * usage['total_used'] // max(budget, 1)}% of budget)")
    print(f"  Input tokens       : {usage['used_input']:,}")
    print(f"  Output tokens      : {usage['used_output']:,}")
    print("=" * 60)
    print("\nRun the graph-guided pipeline for comparison:")
    print(f"  uv run python main.py --budget {budget}")
