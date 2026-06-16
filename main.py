"""EX04 — Reverse Engineering, Debugging, and Token-Efficient Agentic AI.

Entry point: parses the broken-python codebase, builds a knowledge graph,
exports an Obsidian vault, then runs Navigator → Analyzer → Fixer agents
via a LangGraph StateGraph.

Modes:
  default        LangGraph pipeline (Navigator → Analyzer → Fixer)
  --graph-only   Build and export the Obsidian vault, no AI agents
  --improve      Improvement loop: analyze → fix proposals → re-analyze
  --diagram      Print the LangGraph Mermaid diagram and exit
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

TARGET_DEFAULT = str(Path(__file__).parent / "data" / "broken-python")
OBSIDIAN_DEFAULT = str(Path(__file__).parent / "obsidian")


def main() -> None:
    parser = argparse.ArgumentParser(description="EX04: Reverse Engineering with AI Agents (LangGraph)")
    parser.add_argument("--source", default=TARGET_DEFAULT,
                        help="Path to the Python codebase to analyse")
    parser.add_argument("--vault", default=OBSIDIAN_DEFAULT,
                        help="Output directory for the Obsidian vault (default: ./obsidian)")
    parser.add_argument("--budget", type=int, default=60_000,
                        help="Token budget across all agents (default: 60000)")
    parser.add_argument("--graph-only", action="store_true",
                        help="Build and export the graph without calling AI agents")
    parser.add_argument("--improve", action="store_true",
                        help="Run the improvement loop (multiple analysis passes)")
    parser.add_argument("--iterations", type=int, default=2,
                        help="Number of improvement iterations (default: 2)")
    parser.add_argument("--diagram", action="store_true",
                        help="Print the LangGraph Mermaid diagram and exit")
    args = parser.parse_args()

    source = args.source
    if not Path(source).exists():
        print(f"ERROR: source path does not exist: {source}")
        sys.exit(1)

    if args.diagram:
        from src.langgraph_workflow import print_workflow_diagram
        print_workflow_diagram()
        return

    if args.graph_only:
        _run_graph_only(source, args.vault)
        return

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not set — running graph-only mode")
        _run_graph_only(source, args.vault)
        return

    if args.improve:
        _run_improvement_loop(source, args.vault, args.budget, args.iterations)
    else:
        _run_langgraph(source, args.vault, args.budget)


# ── Runners ───────────────────────────────────────────────────────────────────

def _run_langgraph(source: str, vault_dir: str, budget: int) -> None:
    """Run the LangGraph pipeline: build_graph → navigate → analyze → fix."""
    from src.langgraph_workflow import run_workflow

    print(f"[LangGraph] Starting workflow on: {source}")
    print(f"[LangGraph] Vault: {vault_dir}  |  Budget: {budget:,} tokens")
    print(f"[LangGraph] Nodes: build_graph → navigate → analyze → fix\n")

    state = run_workflow(source_root=source, vault_dir=vault_dir, token_budget=budget)

    if state.get("error"):
        print(f"[LangGraph] ERROR: {state['error']}")
        sys.exit(1)

    _save_state(state, vault_dir)
    _print_langgraph_summary(state)


def _run_improvement_loop(source: str, vault_dir: str, budget: int, iterations: int) -> None:
    """Re-run the LangGraph workflow multiple times, reporting change in bug count."""
    from src.langgraph_workflow import run_workflow

    print(f"[LangGraph] Improvement loop: {iterations} iterations\n")
    history = []
    for i in range(1, iterations + 1):
        print(f"{'='*50}")
        print(f"  Iteration {i}/{iterations}")
        print(f"{'='*50}")
        state = run_workflow(source_root=source, vault_dir=vault_dir, token_budget=budget)
        bugs = state.get("bug_report", {}).get("bugs", [])
        fixes = state.get("fix_report", {}).get("fixes", [])
        tokens = state.get("token_usage", {}).get("total_used", 0)
        print(f"  Bugs: {len(bugs)} | Fixes: {len(fixes)} | Tokens: {tokens:,}\n")
        history.append({"iteration": i, "bugs": len(bugs), "fixes": len(fixes), "tokens": tokens})

    out = Path(vault_dir) / "improvement_history.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(f"\n[LangGraph] History saved: {out}")


def _run_graph_only(source: str, vault_dir: str) -> None:
    from src.graph_builder.ast_parser import parse_directory
    from src.graph_builder.graph_generator import KnowledgeGraph
    from src.graph_builder.obsidian_exporter import ObsidianExporter

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


# ── Output helpers ─────────────────────────────────────────────────────────────

def _save_state(state: dict, vault_dir: str) -> None:
    """Persist the final workflow state (excluding the non-serialisable KG)."""
    serialisable = {k: v for k, v in state.items() if k != "knowledge_graph"}
    out = Path(vault_dir) / "analysis_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(serialisable, indent=2, default=str), encoding="utf-8")
    print(f"[LangGraph] Report saved: {out}")


def _print_langgraph_summary(state: dict) -> None:
    print("\n" + "=" * 60)
    print("LANGGRAPH WORKFLOW — FINAL REPORT")
    print("=" * 60)

    m = state.get("graph_summary", {})
    print(f"Graph  : {m.get('node_count', 0)} nodes, {m.get('edge_count', 0)} edges")
    print(f"Bridges: {m.get('bridge_count', 0)}  |  Communities: {m.get('community_count', 0)}")

    bugs = state.get("bug_report", {}).get("bugs", [])
    print(f"\nBugs Found: {len(bugs)}")
    for bug in bugs:
        sev = bug.get("severity", "?").upper()
        btype = bug.get("type", "?")
        nodes = ", ".join(bug.get("affected_nodes", []))
        hint = bug.get("fix_hint", "")
        print(f"  [{sev}] {btype}  →  {nodes}")
        print(f"         Fix: {hint}")

    fixes = state.get("fix_report", {}).get("fixes", [])
    print(f"\nFixes Proposed: {len(fixes)}")
    for fix in fixes:
        print(f"  {fix.get('file_path', '?')} | {fix.get('target_symbol', '')} "
              f"| {fix.get('architectural_pattern', '')} | {fix.get('description', '')}")

    usage = state.get("token_usage", {})
    print(f"\nToken Usage: {usage.get('total_used', 0):,} / {usage.get('budget', 0):,} "
          f"({100*usage.get('total_used',0)//max(usage.get('budget',1),1)}% of budget)")
    print("=" * 60)


if __name__ == "__main__":
    main()
