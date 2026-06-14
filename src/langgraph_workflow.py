"""LangGraph workflow — public API: build_workflow, run_workflow, print_workflow_diagram.

State, routing, and node logic are split into workflow_state.py and workflow_nodes.py.
Everything is re-exported here so existing callers do not need to change imports.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from src.agents.base_agent import AgentBudget
from src.workflow_nodes import (  # noqa: F401
    analyze_node,
    build_graph_node,
    fix_node,
    navigate_node,
    raw_reader_node,
)
from src.workflow_state import (  # noqa: F401
    SPARSE_EDGE_THRESHOLD,
    WorkflowState,
    _fallback_bug_report,
    _route_after_build,
)


def build_workflow(token_budget: int = 60_000) -> tuple[object, AgentBudget]:
    """Construct and compile the LangGraph StateGraph with adaptive routing."""
    budget = AgentBudget(max_tokens=token_budget)
    graph = StateGraph(WorkflowState)

    graph.add_node("build_graph", build_graph_node)
    graph.add_node("navigate",    lambda s: navigate_node(s, budget))
    graph.add_node("raw_reader",  lambda s: raw_reader_node(s, budget))
    graph.add_node("analyze",     lambda s: analyze_node(s, budget))
    graph.add_node("fix",         lambda s: fix_node(s, budget))

    graph.add_edge(START, "build_graph")
    graph.add_conditional_edges(
        "build_graph",
        _route_after_build,
        {"navigate": "navigate", "raw_reader": "raw_reader", "analyze": "analyze"},
    )
    graph.add_edge("navigate",   "analyze")
    graph.add_edge("raw_reader", "analyze")
    graph.add_edge("analyze",    "fix")
    graph.add_edge("fix",        END)

    return graph.compile(), budget


def run_workflow(
    source_root: str,
    vault_dir: str = "obsidian",
    token_budget: int = 60_000,
) -> WorkflowState:
    """Run the full LangGraph workflow and return the final state."""
    workflow, _ = build_workflow(token_budget)
    initial: WorkflowState = {
        "source_root": source_root,
        "vault_dir": vault_dir,
        "knowledge_graph": None,
        "graph_summary": {},
        "raw_files": {},
        "navigation": "",
        "bug_report": {},
        "fix_report": {},
        "token_usage": {},
        "is_sparse": False,
        "error": None,
    }
    return workflow.invoke(initial)


def print_workflow_diagram() -> None:
    """Print the Mermaid diagram of the LangGraph workflow to stdout."""
    workflow, _ = build_workflow()
    print(workflow.get_graph().draw_mermaid())
