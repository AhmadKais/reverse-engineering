"""Improvement loop: apply fixes → rebuild graph → compare metrics."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path


def _run_improvement_loop(source: str, vault_dir: str, budget: int, iterations: int) -> None:
    """Improvement loop: analyze → fix → apply → rebuild graph → compare metrics.

    Each iteration:
      1. Run the full LangGraph pipeline (build_graph → analyze → fix)
      2. Ask the Fixer to generate CORRECTED Python source for each buggy file
      3. Write corrected files to a temp directory
      4. Rebuild the knowledge graph from the corrected files
      5. Compare edge/node counts before vs after — proves the fix worked
    """
    from src.agents.base_agent import AgentBudget
    from src.agents.fixer_agent import FixerAgent
    from src.graph_builder.ast_parser import parse_directory
    from src.graph_builder.graph_generator import KnowledgeGraph
    from src.graph_builder.obsidian_exporter import ObsidianExporter
    from src.langgraph_workflow import run_workflow

    print(f"[improve] Starting improvement loop: {iterations} iteration(s)\n")
    history = []

    for i in range(1, iterations + 1):
        print(f"{'='*55}")
        print(f"  Iteration {i}/{iterations}")
        print(f"{'='*55}")

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

        print("  [apply ] Generating corrected Python files via FixerAgent…")
        fixer_budget = AgentBudget(max_tokens=budget)
        fixer = FixerAgent(fixer_budget)
        corrected = fixer.generate_corrected_files(bug_report, raw_files)

        if not corrected:
            print("  [apply ] No corrected files generated — skipping graph rebuild.")
            after_nodes, after_edges = before_nodes, before_edges
        else:
            tmp = tempfile.mkdtemp(prefix="ex04_improved_")
            try:
                for rel_path, code in corrected.items():
                    out_file = Path(tmp) / rel_path
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                    out_file.write_text(code, encoding="utf-8")
                print(f"  [apply ] Wrote {len(corrected)} corrected file(s) to temp dir")

                after_nodes_list, after_edges_list = parse_directory(tmp)
                after_kg = KnowledgeGraph()
                after_kg.build(after_nodes_list, after_edges_list)
                after_kg.compute_metrics()
                after_nodes = after_kg.metrics.node_count
                after_edges = after_kg.metrics.edge_count

                improved_vault = str(Path(vault_dir).parent / f"obsidian_improved_iter{i}")
                ObsidianExporter(improved_vault).export(after_kg, source_dir=tmp)
                print(f"  [apply ] Improved vault → {improved_vault}/")
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

        delta_nodes = after_nodes - before_nodes
        delta_edges = after_edges - before_edges
        print(f"  [after ] Graph : {after_nodes} nodes, {after_edges} edges")
        print(f"  [delta ] Nodes : {delta_nodes:+d}  |  Edges: {delta_edges:+d}")
        if delta_edges > 0:
            print("  [result] Graph connectivity IMPROVED — fix was effective")
        elif before_edges == 0 and after_edges == 0:
            print("  [result] Files still unparseable after fix — manual review needed")
        else:
            print("  [result] Graph unchanged — bugs may be logic-only (no AST impact)")

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

    out = Path(vault_dir).parent / "artifacts" / "improvement_history.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(f"[improve] History saved: {out}")
    print(f"[improve] Loop complete. Final delta: "
          f"nodes {history[-1]['delta']['nodes']:+d}, "
          f"edges {history[-1]['delta']['edges']:+d}")
