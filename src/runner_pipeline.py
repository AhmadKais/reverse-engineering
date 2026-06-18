"""LangGraph pipeline runner and terminal output helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _run_langgraph(source: str, vault_dir: str, budget: int) -> None:
    """Run the LangGraph pipeline: build_graph → navigate → analyze → fix."""
    from src.langgraph_workflow import run_workflow

    print(f"[LangGraph] Starting workflow on: {source}")
    print(f"[LangGraph] Vault: {vault_dir}  |  Budget: {budget:,} tokens")
    print("[LangGraph] Nodes: build_graph → (navigate|raw_reader) → analyze → fix\n")

    state = run_workflow(source_root=source, vault_dir=vault_dir, token_budget=budget)

    if state.get("error"):
        print(f"[LangGraph] ERROR: {state['error']}")
        sys.exit(1)

    _save_state(state, vault_dir)
    _print_langgraph_summary(state)


def _save_state(state: dict, vault_dir: str) -> None:
    """Persist the final workflow state (excluding the non-serialisable KG)."""
    serialisable = {k: v for k, v in state.items() if k != "knowledge_graph"}
    out = Path(vault_dir).parent / "artifacts" / "analysis_report.json"
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
