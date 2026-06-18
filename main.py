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
    parser.add_argument("--naive", action="store_true",
                        help="Run naive baseline: send ALL files to agents (no graph, no Obsidian)")
    args = parser.parse_args()

    source = args.source
    if not Path(source).exists():
        print(f"ERROR: source path does not exist: {source}")
        sys.exit(1)

    if args.diagram:
        from src.langgraph_workflow import print_workflow_diagram
        print_workflow_diagram()
        return

    if args.naive:
        _run_naive(source, args.budget)
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
    """Improvement loop: analyze → fix → apply → rebuild graph → compare metrics.

    Each iteration:
      1. Run the full LangGraph pipeline (build_graph → analyze → fix)
      2. Ask the Fixer to generate CORRECTED Python source for each buggy file
      3. Write corrected files to a temp directory
      4. Rebuild the knowledge graph from the corrected files
      5. Compare edge/node counts before vs after — proves the fix worked
    """
    import tempfile
    import shutil
    from src.langgraph_workflow import run_workflow
    from src.agents.base_agent import AgentBudget
    from src.agents.fixer_agent import FixerAgent
    from src.graph_builder.ast_parser import parse_directory
    from src.graph_builder.graph_generator import KnowledgeGraph
    from src.graph_builder.obsidian_exporter import ObsidianExporter

    print(f"[improve] Starting improvement loop: {iterations} iteration(s)\n")
    history = []

    for i in range(1, iterations + 1):
        print(f"{'='*55}")
        print(f"  Iteration {i}/{iterations}")
        print(f"{'='*55}")

        # ── Step 1: Full pipeline ──────────────────────────────
        state = run_workflow(source_root=source, vault_dir=vault_dir, token_budget=budget)
        bug_report = state.get("bug_report", {})
        fix_report = state.get("fix_report", {})
        raw_files  = state.get("raw_files", {})
        bugs   = bug_report.get("bugs", [])
        fixes  = fix_report.get("fixes", [])
        tokens = state.get("token_usage", {}).get("total_used", 0)
        before_kg: KnowledgeGraph = state.get("knowledge_graph")  # type: ignore[assignment]
        before_nodes = before_kg.metrics.node_count if before_kg else 0
        before_edges = before_kg.metrics.edge_count if before_kg else 0

        print(f"  [before] Graph : {before_nodes} nodes, {before_edges} edges")
        print(f"  [before] Bugs  : {len(bugs)}  |  Fixes: {len(fixes)}  |  Tokens: {tokens:,}")

        # ── Step 2: Generate corrected source files ────────────
        print(f"  [apply ] Generating corrected Python files via FixerAgent…")
        fixer_budget = AgentBudget(max_tokens=budget)
        fixer = FixerAgent(fixer_budget)
        corrected = fixer.generate_corrected_files(bug_report, raw_files)

        if not corrected:
            print("  [apply ] No corrected files generated — skipping graph rebuild.")
            after_nodes, after_edges = before_nodes, before_edges
        else:
            # ── Step 3: Write corrected files to a temp dir ───────
            tmp = tempfile.mkdtemp(prefix="ex04_improved_")
            try:
                for rel_path, code in corrected.items():
                    out_file = Path(tmp) / rel_path
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                    out_file.write_text(code, encoding="utf-8")
                print(f"  [apply ] Wrote {len(corrected)} corrected file(s) to temp dir")

                # ── Step 4: Rebuild graph from corrected files ────────
                after_nodes_list, after_edges_list = parse_directory(tmp)
                after_kg = KnowledgeGraph()
                after_kg.build(after_nodes_list, after_edges_list)
                after_kg.compute_metrics()
                after_nodes = after_kg.metrics.node_count
                after_edges = after_kg.metrics.edge_count

                # Export the improved vault so it's visible in Obsidian
                improved_vault = str(Path(vault_dir).parent / f"obsidian_improved_iter{i}")
                ObsidianExporter(improved_vault).export(after_kg, source_dir=tmp)
                print(f"  [apply ] Improved vault → {improved_vault}/")
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

        # ── Step 5: Compare metrics ────────────────────────────
        delta_nodes = after_nodes - before_nodes
        delta_edges = after_edges - before_edges
        print(f"  [after ] Graph : {after_nodes} nodes, {after_edges} edges")
        print(f"  [delta ] Nodes : {delta_nodes:+d}  |  Edges: {delta_edges:+d}")
        if delta_edges > 0:
            print(f"  [result] ✓ Graph connectivity IMPROVED — fix was effective")
        elif before_edges == 0 and after_edges == 0:
            print(f"  [result] Files still unparseable after fix — manual review needed")
        else:
            print(f"  [result] Graph unchanged — bugs may be logic-only (no AST impact)")

        history.append({
            "iteration": i,
            "bugs": len(bugs),
            "fixes": len(fixes),
            "tokens": tokens,
            "corrected_files": len(corrected) if corrected else 0,
            "before": {"nodes": before_nodes, "edges": before_edges},
            "after":  {"nodes": after_nodes,  "edges": after_edges},
            "delta":  {"nodes": delta_nodes,   "edges": delta_edges},
        })
        print()

    # ── Save history ───────────────────────────────────────────
    out = Path(vault_dir) / "improvement_history.json"
    out.write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(f"[improve] History saved: {out}")
    print(f"[improve] Loop complete. Final delta: "
          f"nodes {history[-1]['delta']['nodes']:+d}, "
          f"edges {history[-1]['delta']['edges']:+d}")


def _run_naive(source: str, budget: int) -> None:
    """Naive baseline: send ALL .py files to every agent with no graph routing.

    Contrast with the graph-guided pipeline:
    - No KnowledgeGraph built
    - No Obsidian vault consulted
    - No sparse/dense detection
    - No targeted file selection
    Every file is concatenated and sent in full to Analyzer then Fixer.
    Token counts from this run feed TOKEN_COMPARISON.md.
    """
    from src.agents.base_agent import AgentBudget
    from src.agents.analyzer_agent import AnalyzerAgent
    from src.agents.fixer_agent import FixerAgent

    print(f"[naive] Starting naive baseline on: {source}")
    print(f"[naive] Budget: {budget:,} tokens")
    print("[naive] Mode: ALL files → Analyzer → Fixer (no graph, no Obsidian)\n")

    # Read every .py file without any filtering
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
