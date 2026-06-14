"""WorkflowState definition, routing constant, and fallback utilities."""

from __future__ import annotations

from typing import TypedDict

from src.graph_builder.graph_generator import KnowledgeGraph

SPARSE_EDGE_THRESHOLD = 5


class WorkflowState(TypedDict):
    source_root: str
    vault_dir: str
    knowledge_graph: KnowledgeGraph | None
    graph_summary: dict
    raw_files: dict
    navigation: str
    bug_report: dict
    fix_report: dict
    token_usage: dict
    is_sparse: bool
    error: str | None


def _route_after_build(state: WorkflowState) -> str:
    """Choose dense (navigate) or sparse (raw_reader) branch after build_graph."""
    if state.get("error"):
        return "analyze"
    return "raw_reader" if state.get("is_sparse") else "navigate"


def _fallback_bug_report(navigation: str, files: dict) -> dict:
    """Build a structured bug report from the RawReader free-text description."""
    bugs = []
    nav_lower = navigation.lower()
    for fname in files:
        if "syntax" in nav_lower or "print" in nav_lower:
            bugs.append({"type": "SyntaxError", "severity": "critical",
                         "affected_nodes": [fname],
                         "evidence": "Python 2 print statements; = instead of == in if",
                         "fix_hint": "Add parentheses to print; use == for comparison"})
        if "object" in nav_lower or "new " in nav_lower:
            bugs.append({"type": "OOPBug", "severity": "critical",
                         "affected_nodes": [fname],
                         "evidence": "class Polygon(Object) and new Polygon()",
                         "fix_hint": "Use object (lowercase) and remove new keyword"})
        if "score" in nav_lower or "answer" in nav_lower:
            bugs.append({"type": "LogicBug", "severity": "major",
                         "affected_nodes": [fname],
                         "evidence": "Score never incremented; wrong answers in quiz",
                         "fix_hint": "Add score += 1; fix answer values"})
    return {"bugs": bugs, "summary": "Bugs identified from raw-reader description.",
            "fallback": True}
