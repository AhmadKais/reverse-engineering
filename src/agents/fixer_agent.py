"""Fixer Agent — proposes and applies targeted code patches for architectural bugs.

For each bug from the Analyzer's report, the Fixer:
  1. Reads the affected file(s)
  2. Generates a concrete refactoring patch
  3. Optionally writes the patch back to disk (improvement loop)

The Fixer does NOT blindly rewrite files — it produces minimal surgical changes
that address the specific architectural issue without changing surrounding logic.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.agents.base_agent import AgentBudget, BaseAgent

_SYSTEM_PROMPT = """\
You are the Fixer — a senior refactoring engineer.
Given a bug report and relevant code, you produce a structured remediation plan.

IMPORTANT: Do NOT include any code inside the JSON values — only descriptions.
Keeping code out of JSON prevents escaping bugs.

For each bug, output EXACTLY this JSON structure:
{
  "fixes": [
    {
      "bug_type": "SPOF | GodObject | Bottleneck | MissingAbstraction | HardcodedDispatch",
      "file_path": "relative/path/to/file.py",
      "target_symbol": "ClassName or function_name to modify",
      "description": "what this fix does in one clear sentence",
      "architectural_pattern": "design pattern that solves this (e.g. Factory, Strategy, CircuitBreaker)",
      "new_class_or_method": "name of new class/method to introduce (if any)",
      "explanation": "why this fixes the root cause — the architectural insight"
    }
  ],
  "overall_impact": "how these fixes collectively improve the architecture in 2 sentences"
}

Output ONLY valid JSON. No markdown. No code inside JSON values.
"""


class FixerAgent(BaseAgent):
    """Generates and optionally applies architectural refactoring patches."""

    def __init__(self, budget: AgentBudget) -> None:
        super().__init__(
            name="Fixer",
            system_prompt=_SYSTEM_PROMPT,
            budget=budget,
            max_tokens=3000,
        )

    def propose_fixes(self, bug_report: dict, source_root: str) -> dict:
        """Generate fix proposals for all bugs in the report."""
        bugs = bug_report.get("bugs", [])
        if not bugs:
            return {"fixes": [], "overall_impact": "No bugs to fix."}

        snippets = self._read_affected_code(bugs, source_root)
        prompt = (
            "Generate surgical code patches for these architectural bugs.\n\n"
            f"Bug Report:\n```json\n{json.dumps(bugs, indent=2)}\n```\n\n"
            f"Affected Code:\n{snippets}\n\n"
            "Produce minimal patches that fix each bug. Output ONLY valid JSON."
        )
        self.reset_history()
        raw = self.generate_response(prompt)
        return self._parse_fixes(raw)

    def apply_fixes(self, fix_report: dict, source_root: str, dry_run: bool = True) -> list[str]:
        """Report what changes would be made (dry_run=True) or log them (dry_run=False).

        The new schema uses description-only fixes (no verbatim code patches),
        so this method generates a structured action log rather than mutating files.
        File-level mutations are deferred to the improvement loop.
        """
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

    def _read_affected_code(self, bugs: list[dict], source_root: str) -> str:
        """Read code from files mentioned in bug reports (capped at 600 chars each)."""
        seen_files: set[str] = set()
        snippets: list[str] = []
        for bug in bugs:
            for node_name in bug.get("affected_nodes", []):
                # Find any .py file in source_root that contains the class/function
                for py_file in Path(source_root).rglob("*.py"):
                    if py_file in seen_files:
                        continue
                    try:
                        content = py_file.read_text(encoding="utf-8")
                        if f"class {node_name}" in content or f"def {node_name}" in content:
                            seen_files.add(py_file)
                            snippets.append(
                                f"### {py_file.name}\n```python\n{content[:600]}\n```"
                            )
                            break
                    except OSError:
                        pass
        return "\n\n".join(snippets) if snippets else "No code files found for affected nodes."

    def _parse_fixes(self, raw: str) -> dict:
        """Parse LLM JSON response into structured fix report.

        Three-stage: strip fences → json.loads → embedded scan.
        """
        text = self._strip_fences(raw)
        # Stage 1: direct parse
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "fixes" in data:
                return data
        except json.JSONDecodeError:
            pass
        # Stage 2: scan for the first valid JSON object
        decoder = json.JSONDecoder()
        for i in range(len(text)):
            if text[i] == "{":
                try:
                    data, _ = decoder.raw_decode(text, i)
                    if isinstance(data, dict) and "fixes" in data:
                        return data
                except json.JSONDecodeError:
                    continue
        return {"fixes": [], "overall_impact": raw[:300], "parse_error": True}

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Remove markdown code fences (```json ... ``` or ``` ... ```)."""
        t = text.strip()
        if t.startswith("```"):
            lines = t.split("\n")
            inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            return "\n".join(inner).strip()
        return t
