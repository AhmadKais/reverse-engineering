"""Parsing helpers and system prompt for FixerAgent — no class state required."""

from __future__ import annotations

import json
import re
from pathlib import Path

FIXER_SYSTEM_PROMPT = """\
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
      "architectural_pattern": "design pattern (e.g. Factory, Strategy, CircuitBreaker)",
      "new_class_or_method": "name of new class/method to introduce (if any)",
      "explanation": "why this fixes the root cause — the architectural insight"
    }
  ],
  "overall_impact": "how these fixes collectively improve the architecture in 2 sentences"
}

Output ONLY valid JSON. No markdown. No code inside JSON values.
"""


def strip_fences(text: str) -> str:
    """Remove markdown code fences (```json ... ``` or ``` ... ```)."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        return "\n".join(inner).strip()
    return t


def parse_fixes(raw: str) -> dict:
    """Parse LLM JSON response into structured fix report.

    Three-stage: strip fences → json.loads → embedded scan.
    """
    text = strip_fences(raw)
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "fixes" in data:
            return data
    except json.JSONDecodeError:
        pass
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


def parse_corrected_files(raw: str) -> dict[str, str]:
    """Parse FILE/---BEGIN---/---END--- blocks from generate_corrected_files output."""
    files: dict[str, str] = {}
    pattern = re.compile(
        r"FILE:\s*(.+?)\s*\n---BEGIN---\n(.*?)\n---END---",
        re.DOTALL,
    )
    for m in pattern.finditer(raw):
        filename = m.group(1).strip()
        code = m.group(2)
        files[filename] = code
    return files


def read_affected_code(bugs: list[dict], source_root: str) -> str:
    """Read code from files mentioned in bug reports (capped at 600 chars each)."""
    seen_files: set[Path] = set()
    snippets: list[str] = []
    for bug in bugs:
        for node_name in bug.get("affected_nodes", []):
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
