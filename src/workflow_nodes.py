"""LangGraph node implementations — each node is a pure function on WorkflowState."""

from __future__ import annotations

import contextlib
import json
from pathlib import Path

from src.agents.analyzer_agent import AnalyzerAgent
from src.agents.base_agent import AgentBudget, BaseAgent
from src.agents.fixer_agent import FixerAgent
from src.agents.navigator_agent import NavigatorAgent
from src.graph_builder.ast_parser import parse_directory
from src.graph_builder.graph_generator import KnowledgeGraph
from src.graph_builder.obsidian_exporter import ObsidianExporter
from src.workflow_state import SPARSE_EDGE_THRESHOLD, WorkflowState, _fallback_bug_report


def build_graph_node(state: WorkflowState) -> WorkflowState:
    """Node 1: parse codebase → build KnowledgeGraph → export Obsidian vault."""
    try:
        nodes, edges = parse_directory(state["source_root"])
        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        kg.compute_metrics()
        ObsidianExporter(state["vault_dir"]).export(kg)

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
    """Node 2 (dense path): Navigator reads graph summary → architectural overview."""
    if state.get("error"):
        return state
    try:
        agent = NavigatorAgent(budget)
        navigation = agent.navigate(state["knowledge_graph"])
        return {**state, "navigation": navigation, "token_usage": budget.status()}
    except Exception as exc:
        return {**state, "error": f"navigate_node failed: {exc}"}


def raw_reader_node(state: WorkflowState, budget: AgentBudget) -> WorkflowState:
    """Node 2 (sparse path): read raw file content and describe structure."""
    if state.get("error"):
        return state
    try:
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
        navigation = agent.generate_response(
            f"Describe the structure and bugs in these Python files:\n\n{files_text}"
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


def _analyze_raw(state: WorkflowState, budget: AgentBudget) -> dict:
    """Sparse-mode analysis: send raw file text directly to AnalyzerAgent."""
    agent = AnalyzerAgent(budget)
    main_files = {
        k: v for k, v in state["raw_files"].items()
        if "step" not in k and k.endswith(".py")
    } or state["raw_files"]

    files_text = "\n\n".join(
        f"### {fname}\n```python\n{content[:1000]}\n```"
        for fname, content in main_files.items()
    )
    prompt = (
        "You are auditing Python code for bugs. List every bug — syntax errors, "
        "logic errors, wrong values, OOP mistakes.\n\n"
        f"Code to audit:\n{files_text}\n\n"
        "Respond with raw JSON only (no markdown fences):\n"
        '{"bugs":[{"type":"SyntaxError","severity":"critical",'
        '"affected_nodes":["file.py"],"evidence":"line or pattern","fix_hint":"fix"}],'
        '"summary":"one sentence"}'
    )
    agent.reset_history()
    raw = agent.generate_response(prompt)
    result = agent._parse_report(raw)

    if result.get("parse_error") or not result.get("bugs"):
        result = _fallback_bug_report(state["navigation"], main_files)

    return result


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


def _fix_raw(state: WorkflowState, budget: AgentBudget, agent: FixerAgent) -> dict:
    """Sparse-mode fix: generate corrected file content via FixerAgent."""
    bugs = state["bug_report"].get("bugs", [])
    files_text = "\n\n".join(
        f"### {fname}\n```python\n{content}\n```"
        for fname, content in state["raw_files"].items()
    )
    prompt = (
        "Fix ALL bugs in these Python files. For each file produce a fully corrected version.\n\n"
        f"Bug report:\n{json.dumps(bugs, indent=2)}\n\n"
        f"Source files:\n{files_text}\n\n"
        "Output ONLY valid JSON (no markdown fences, no code blocks inside JSON values):\n"
        '{"fixes": [{"bug_type": "...", "file_path": "relative/path.py", '
        '"target_symbol": "function or class name", '
        '"description": "what was fixed", '
        '"architectural_pattern": "pattern applied", '
        '"new_class_or_method": "if any", '
        '"explanation": "why this fixes the root cause"}], '
        '"overall_impact": "summary"}'
    )
    agent.reset_history()
    raw = agent.generate_response(prompt)
    return agent._parse_fixes(raw)
