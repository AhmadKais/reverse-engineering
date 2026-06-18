"""LangGraph node implementations — each node is a pure function on WorkflowState."""

from __future__ import annotations

import contextlib
from pathlib import Path

from src.agents.analyzer_agent import AnalyzerAgent
from src.agents.base_agent import AgentBudget, BaseAgent
from src.agents.fixer_agent import FixerAgent
from src.agents.navigator_agent import NavigatorAgent
from src.graph_builder.ast_parser import parse_directory
from src.graph_builder.graph_generator import KnowledgeGraph
from src.graph_builder.obsidian_exporter import ObsidianExporter
from src.workflow_helpers import _analyze_raw, _fix_raw, _read_vault_pages
from src.workflow_state import SPARSE_EDGE_THRESHOLD, WorkflowState


def build_graph_node(state: WorkflowState) -> WorkflowState:
    """Node 1: parse codebase → build KnowledgeGraph → export Obsidian vault."""
    try:
        nodes, edges = parse_directory(state["source_root"])
        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        kg.compute_metrics()
        ObsidianExporter(state["vault_dir"]).export(kg, source_dir=state["source_root"])

        is_sparse = kg.metrics.edge_count < SPARSE_EDGE_THRESHOLD
        raw_files: dict = {}
        if is_sparse:
            for py_file in Path(state["source_root"]).rglob("*.py"):
                with contextlib.suppress(OSError):
                    raw_files[str(py_file.relative_to(state["source_root"]))] = \
                        py_file.read_text(encoding="utf-8", errors="replace")

        return {
            **state,
            "knowledge_graph": kg,
            "graph_summary": kg.summary_dict(),
            "raw_files": raw_files,
            "is_sparse": is_sparse,
            "error": None,
        }
    except Exception as exc:
        return {**state, "error": f"build_graph_node failed: {exc}"}


def navigate_node(state: WorkflowState, budget: AgentBudget) -> WorkflowState:
    """Node 2 (dense path): Navigator reads Obsidian vault pages first, then graph summary."""
    if state.get("error"):
        return state
    try:
        vault_context = _read_vault_pages(state["vault_dir"])
        agent = NavigatorAgent(budget)
        navigation = agent.navigate(state["knowledge_graph"], vault_context=vault_context)
        return {**state, "navigation": navigation, "token_usage": budget.status()}
    except Exception as exc:
        return {**state, "error": f"navigate_node failed: {exc}"}


def raw_reader_node(state: WorkflowState, budget: AgentBudget) -> WorkflowState:
    """Node 2 (sparse path): use hot.md as graph signal, then read raw file content."""
    if state.get("error"):
        return state
    try:
        vault_context = _read_vault_pages(state["vault_dir"])
        system = (
            "You are a Python code reader. Given raw source files that contain "
            "bugs (possibly Python 2 syntax, logic errors, or undefined names), "
            "describe the INTENDED structure: what each file is trying to do, "
            "its functions/classes, and any obvious bugs you can see from reading "
            "the raw text.\n\n"
            "Format:\n## File: <name>\n**Intent**: ...\n**Structure**: ...\n**Visible bugs**: ..."
        )
        agent = BaseAgent(name="RawReader", system_prompt=system, budget=budget, max_tokens=1200)
        files_text = "\n\n".join(
            f"### {fname}\n```python\n{content[:1500]}\n```"
            for fname, content in state["raw_files"].items()
        )
        graph_preamble = (
            f"{vault_context}\n\n"
            "The graph above shows a SPARSE graph (all betweenness = 0, 0 edges). "
            "This means the main source files failed AST parsing — syntax errors prevent "
            "the graph builder from reading them. The files below are the ones that failed.\n\n"
            if vault_context else ""
        )
        navigation = agent.generate_response(
            f"{graph_preamble}Describe the structure and bugs in these Python files:\n\n{files_text}"
        )
        return {**state, "navigation": navigation, "token_usage": budget.status()}
    except Exception as exc:
        return {**state, "error": f"raw_reader_node failed: {exc}"}


def analyze_node(state: WorkflowState, budget: AgentBudget) -> WorkflowState:
    """Node 3: Analyzer reads description → structured bug report."""
    if state.get("error"):
        return state
    try:
        if state.get("is_sparse"):
            bug_report = _analyze_raw(state, budget)
        else:
            agent = AnalyzerAgent(budget)
            bug_report = agent.analyze(state["knowledge_graph"], state["source_root"])
        return {**state, "bug_report": bug_report, "token_usage": budget.status()}
    except Exception as exc:
        return {**state, "error": f"analyze_node failed: {exc}"}


def fix_node(state: WorkflowState, budget: AgentBudget) -> WorkflowState:
    """Node 4: Fixer reads bug report → proposes fixes."""
    if state.get("error"):
        return state
    try:
        agent = FixerAgent(budget)
        if state.get("is_sparse"):
            fix_report = _fix_raw(state, budget, agent)
        else:
            fix_report = agent.propose_fixes(state["bug_report"], state["source_root"])
        return {**state, "fix_report": fix_report, "token_usage": budget.status()}
    except Exception as exc:
        return {**state, "error": f"fix_node failed: {exc}"}
