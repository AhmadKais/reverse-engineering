"""Private helpers for LangGraph node implementations."""

from __future__ import annotations

import contextlib
import json
from pathlib import Path

from src.agents.analyzer_agent import AnalyzerAgent
from src.agents.base_agent import AgentBudget
from src.agents.fixer_agent import FixerAgent
from src.workflow_state import WorkflowState, _fallback_bug_report


def _read_vault_pages(vault_dir: str) -> str:
    """Read hot.md and index.md from the Obsidian vault as the graph-guided entry point.

    Returns empty string if the vault doesn't exist yet (e.g. in unit tests).
    The agent always reads Obsidian pages BEFORE touching source code — this is
    the core graph-guided approach required by the assignment.
    """
    vault = Path(vault_dir)
    parts = []
    for fname in ("hot.md", "index.md"):
        path = vault / fname
        with contextlib.suppress(Exception):
            if path.exists():
                parts.append(
                    f"### {fname} (from Obsidian vault)\n{path.read_text(encoding='utf-8')}"
                )
    return "\n\n".join(parts)


def _analyze_raw(state: WorkflowState, budget: AgentBudget) -> dict:
    """Sparse-mode analysis: raw_reader description + raw file text → AnalyzerAgent."""
    agent = AnalyzerAgent(budget)
    main_files = {
        k: v for k, v in state["raw_files"].items()
        if "step" not in k and k.endswith(".py")
    } or state["raw_files"]

    files_text = "\n\n".join(
        f"### {fname}\n```python\n{content}\n```"
        for fname, content in main_files.items()
    )
    reader_context = (
        f"## Raw Reader Analysis\n\n{state['navigation']}\n\n"
        if state.get("navigation") else ""
    )
    prompt = (
        f"{reader_context}"
        "You are auditing Python code for bugs. Using the reader analysis above "
        "and the source files below, list EVERY bug — syntax errors, logic errors, "
        "wrong values, OOP mistakes.\n\n"
        f"Source files:\n{files_text}\n\n"
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
