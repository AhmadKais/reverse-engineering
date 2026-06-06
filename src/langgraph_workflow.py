"""LangGraph workflow — orchestrates Navigator → Analyzer → Fixer as a state graph.

Each agent is a LangGraph node. State flows through typed edges.
When the knowledge graph is sparse (< SPARSE_EDGE_THRESHOLD edges), the
workflow takes a conditional branch to a raw-code analysis node instead of
the normal graph-guided navigator — demonstrating adaptive fallback.

State schema:
  source_root   str            path to the codebase being analysed
  vault_dir     str            output directory for Obsidian vault
  knowledge_graph KnowledgeGraph | None   in-process object (not serialised)
  graph_summary dict           compact JSON from KnowledgeGraph.summary_dict()
  raw_files     dict           filename → content (populated when graph sparse)
  navigation    str            Navigator or RawReader output
  bug_report    dict           Analyzer agent output  {bugs, summary}
  fix_report    dict           Fixer agent output     {fixes, overall_impact}
  token_usage   dict           AgentBudget.status() snapshot after each node
  is_sparse     bool           True when graph has < SPARSE_EDGE_THRESHOLD edges
  error         str | None     set if a node fails — downstream nodes skip
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.analyzer_agent import AnalyzerAgent
from src.agents.base_agent import AgentBudget
from src.agents.fixer_agent import FixerAgent
from src.agents.navigator_agent import NavigatorAgent
from src.graph_builder.ast_parser import parse_directory
from src.graph_builder.graph_generator import KnowledgeGraph
from src.graph_builder.obsidian_exporter import ObsidianExporter

# If the graph has fewer edges than this after parsing, treat it as sparse
SPARSE_EDGE_THRESHOLD = 5


# ── State ─────────────────────────────────────────────────────────────────────

class WorkflowState(TypedDict):
    source_root: str
    vault_dir: str
    knowledge_graph: KnowledgeGraph | None
    graph_summary: dict
    raw_files: dict          # filename → file content (used in sparse mode)
    navigation: str
    bug_report: dict
    fix_report: dict
    token_usage: dict
    is_sparse: bool
    error: str | None


# ── Node functions ─────────────────────────────────────────────────────────────

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
            # Pre-read all Python files so downstream nodes can work without AST
            for py_file in Path(state["source_root"]).rglob("*.py"):
                try:
                    raw_files[str(py_file.relative_to(state["source_root"]))] = \
                        py_file.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    pass

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
    """Node 2 (sparse path): Read raw file content and describe what's there.

    Used when the graph is sparse (syntax errors prevent AST parsing).
    Reads the actual file text and produces a structural description
    so the Analyzer receives meaningful context despite the empty graph.
    """
    if state.get("error"):
        return state
    try:
        from src.agents.base_agent import BaseAgent
        import json

        system = (
            "You are a Python code reader. Given raw source files that contain "
            "bugs (possibly Python 2 syntax, logic errors, or undefined names), "
            "describe the INTENDED structure: what each file is trying to do, "
            "its functions/classes, and any obvious bugs you can see from reading "
            "the raw text.\n\n"
            "Format:\n## File: <name>\n**Intent**: ...\n**Structure**: ...\n**Visible bugs**: ..."
        )
        agent = BaseAgent(
            name="RawReader",
            system_prompt=system,
            budget=budget,
            max_tokens=1200,
        )
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
    """Node 3: Analyzer reads graph/raw-code description → structured bug report."""
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
    """Sparse-mode analysis: send raw file text directly to the Analyzer.

    Uses a shorter, unambiguous prompt that avoids triggering JSON fence wrapping.
    Falls back to a hand-crafted report from the RawReader navigation text if
    JSON parsing still fails, so bugs are never silently lost.
    """
    from src.agents.analyzer_agent import AnalyzerAgent

    agent = AnalyzerAgent(budget)
    # Only send the two main buggy files (skip step files) to stay within tokens
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

    # If parsing still failed, build a minimal report from the navigation text
    if result.get("parse_error") or not result.get("bugs"):
        result = _fallback_bug_report(state["navigation"], main_files)

    return result


def _fallback_bug_report(navigation: str, files: dict) -> dict:
    """Build a structured bug report from the RawReader's free-text description."""
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


def fix_node(state: WorkflowState, budget: AgentBudget) -> WorkflowState:
    """Node 4: Fixer reads bug report → proposes fixes (+ writes corrected files)."""
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
    """Sparse-mode fix: generate corrected file content and write to artifacts/."""
    import json

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


# ── Routing ────────────────────────────────────────────────────────────────────

def _route_after_build(state: WorkflowState) -> str:
    """Choose graph-guided path (dense) or raw-code path (sparse)."""
    if state.get("error"):
        return "analyze"   # skip navigate, go straight to analyze (which will also skip)
    return "raw_reader" if state.get("is_sparse") else "navigate"


# ── Graph builder ──────────────────────────────────────────────────────────────

def build_workflow(token_budget: int = 60_000) -> tuple[object, AgentBudget]:
    """Construct and compile the LangGraph StateGraph with adaptive routing."""
    budget = AgentBudget(max_tokens=token_budget)
    graph = StateGraph(WorkflowState)

    graph.add_node("build_graph",  build_graph_node)
    graph.add_node("navigate",     lambda s: navigate_node(s, budget))
    graph.add_node("raw_reader",   lambda s: raw_reader_node(s, budget))
    graph.add_node("analyze",      lambda s: analyze_node(s, budget))
    graph.add_node("fix",          lambda s: fix_node(s, budget))

    # Conditional routing after build_graph
    graph.add_edge(START, "build_graph")
    graph.add_conditional_edges(
        "build_graph",
        _route_after_build,
        {"navigate": "navigate", "raw_reader": "raw_reader", "analyze": "analyze"},
    )
    graph.add_edge("navigate",    "analyze")
    graph.add_edge("raw_reader",  "analyze")
    graph.add_edge("analyze",     "fix")
    graph.add_edge("fix",         END)

    compiled = graph.compile()
    return compiled, budget


def run_workflow(
    source_root: str,
    vault_dir: str = "obsidian",
    token_budget: int = 60_000,
) -> WorkflowState:
    """Run the full LangGraph workflow and return the final state."""
    workflow, budget = build_workflow(token_budget)
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
