"""Fixer Agent — proposes and applies targeted code patches for architectural bugs.

For each bug from the Analyzer's report, the Fixer:
  1. Reads the affected file(s)
  2. Generates a concrete refactoring patch
  3. Optionally writes the patch back to disk (improvement loop)
"""

from __future__ import annotations

import json

from src.agents.base_agent import AgentBudget, BaseAgent
from src.agents.fixer_parsers import (
    FIXER_SYSTEM_PROMPT,
    parse_corrected_files,
    parse_fixes,
    read_affected_code,
)
from src.agents.gatekeeper import AgentConfig


class FixerAgent(BaseAgent):
    """Generates and optionally applies architectural refactoring patches."""

    def __init__(self, budget: AgentBudget) -> None:
        """Initialise with a shared budget; sets model max_tokens for fix generation."""
        super().__init__(
            name="Fixer",
            system_prompt=FIXER_SYSTEM_PROMPT,
            budget=budget,
            max_tokens=AgentConfig().max_tokens_for("fixer"),
        )

    def propose_fixes(self, bug_report: dict, source_root: str) -> dict:
        """Generate fix proposals for all bugs in the report."""
        bugs = bug_report.get("bugs", [])
        if not bugs:
            return {"fixes": [], "overall_impact": "No bugs to fix."}

        snippets = read_affected_code(bugs, source_root)
        prompt = (
            "Generate surgical code patches for these architectural bugs.\n\n"
            f"Bug Report:\n```json\n{json.dumps(bugs, indent=2)}\n```\n\n"
            f"Affected Code:\n{snippets}\n\n"
            "Produce minimal patches that fix each bug. Output ONLY valid JSON."
        )
        self.reset_history()
        raw = self.generate_response(prompt)
        return self._parse_fixes(raw)

    def propose_fixes_raw(self, bug_report: dict, file_contents: str) -> dict:
        """Naive mode: propose fixes with all files in context — no targeted snippet selection.

        Used for the token-efficiency baseline comparison. Every file is included regardless
        of relevance; there is no graph-guided targeting.
        """
        bugs = bug_report.get("bugs", [])
        if not bugs:
            return {"fixes": [], "overall_impact": "No bugs to fix."}
        prompt = (
            "Generate surgical code patches for these architectural bugs.\n\n"
            f"Bug Report:\n```json\n{json.dumps(bugs, indent=2)}\n```\n\n"
            f"All Source Files:\n{file_contents}\n\n"
            "Produce minimal patches that fix each bug. Output ONLY valid JSON."
        )
        self.reset_history()
        raw = self.generate_response(prompt)
        return self._parse_fixes(raw)

    def generate_corrected_files(self, bug_report: dict, raw_files: dict) -> dict[str, str]:
        """Generate fully corrected Python source for each buggy file.

        Used by the improvement loop: applies the fix proposals as actual code so
        the graph can be rebuilt and metrics compared before vs after.
        Returns {relative_path: corrected_source}.

        Uses a FILE/---BEGIN---/---END--- delimiter format to avoid JSON escaping.
        """
        bugs = bug_report.get("bugs", [])
        if not bugs:
            return {}
        main_files = {k: v for k, v in raw_files.items() if "step" not in k}
        files_text = "\n\n".join(
            f"FILE: {fname}\n---BEGIN---\n{content}\n---END---"
            for fname, content in main_files.items()
        )
        prompt = (
            "You are a Python bug fixer. Fix ALL bugs listed below in the source files.\n\n"
            f"Bugs to fix:\n{json.dumps(bugs, indent=2)}\n\n"
            f"Source files:\n{files_text}\n\n"
            "Output the COMPLETE corrected Python source for each file using this exact format:\n"
            "FILE: <same filename as above>\n"
            "---BEGIN---\n"
            "<complete corrected python source>\n"
            "---END---\n\n"
            "Include every line of the file. Do not truncate. No explanation outside the blocks."
        )
        self.reset_history()
        raw = self.generate_response(prompt)
        return self._parse_corrected_files(raw)

    def apply_fixes(self, fix_report: dict, source_root: str, dry_run: bool = True) -> list[str]:
        """Report what changes would be made (dry_run=True) or log them (dry_run=False)."""
        results: list[str] = []
        for fix in fix_report.get("fixes", []):
            file_path = fix.get("file_path", "?")
            description = fix.get("description", "")
            pattern = fix.get("architectural_pattern", "")
            symbol = fix.get("target_symbol", "")
            prefix = "DRY-RUN" if dry_run else "PLAN"
            results.append(
                f"[{prefix}] {file_path} → {symbol}: {description} (pattern: {pattern})"
            )
        return results

    def _parse_fixes(self, raw: str) -> dict:
        """Delegate JSON fix-report parsing to fixer_parsers."""
        return parse_fixes(raw)

    def _parse_corrected_files(self, raw: str) -> dict[str, str]:
        """Delegate FILE/BEGIN/END block parsing to fixer_parsers."""
        return parse_corrected_files(raw)

    def _strip_fences(self, text: str) -> str:
        """Remove markdown code fences from LLM output."""
        from src.agents.fixer_parsers import strip_fences
        return strip_fences(text)

    def _read_affected_code(self, bugs: list[dict], source_root: str) -> str:
        """Collect source snippets for nodes affected by the given bug list."""
        return read_affected_code(bugs, source_root)
