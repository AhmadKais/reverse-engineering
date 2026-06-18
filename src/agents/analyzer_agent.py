"""Analyzer Agent — identifies architectural bugs from graph topology + code snippets.

Bugs it hunts:
  1. Single Point of Failure (SPOF) — a hub with no fallback path
  2. God Object — a class/module doing too many things (high out-degree)
  3. Bottleneck — a node every critical path passes through (high betweenness)
  4. Missing Abstraction — concrete coupling where an interface should exist
  5. Hardcoded Dispatch — extensibility blocked by closed switch/if statements

For each bug found, the Analyzer produces a structured report with:
  - Bug type, severity (critical/major/minor)
  - Affected nodes
  - Evidence from the graph (centrality scores, degree counts)
  - Short code snippet confirming the pattern
"""

from __future__ import annotations

import json
from pathlib import Path

from src.agents.base_agent import AgentBudget, BaseAgent
from src.graph_builder.graph_generator import KnowledgeGraph

_SYSTEM_PROMPT = """\
You are the Analyzer — a senior software architect and code reviewer.
Given a knowledge graph summary and targeted code snippets, you identify
architectural bugs and anti-patterns.

For each bug, output a JSON object in this format:
{
  "bugs": [
    {
      "type": "SPOF | GodObject | Bottleneck | MissingAbstraction | HardcodedDispatch",
      "severity": "critical | major | minor",
      "affected_nodes": ["NodeName", ...],
      "evidence": "what in the graph/code confirms this",
      "fix_hint": "one-sentence fix direction"
    }
  ],
  "summary": "2-sentence overall assessment"
}

Output ONLY the JSON. No markdown fences.
"""


class AnalyzerAgent(BaseAgent):
    """Identifies architectural bugs by cross-referencing graph metrics with code."""

    def __init__(self, budget: AgentBudget) -> None:
        """Initialise with a shared budget; sets model max_tokens for bug analysis."""
        super().__init__(
            name="Analyzer",
            system_prompt=_SYSTEM_PROMPT,
            budget=budget,
            max_tokens=2000,
        )

    def analyze(self, kg: KnowledgeGraph, source_root: str) -> dict:
        """Run full architectural analysis; return structured bug report."""
        summary = kg.summary_dict()
        snippets = self._collect_snippets(kg, source_root)

        prompt = (
            "Analyze this Python codebase for architectural bugs.\n\n"
            f"Graph Summary:\n```json\n{json.dumps(summary, indent=2)}\n```\n\n"
            f"Key Code Snippets:\n{snippets}\n\n"
            "Identify all architectural bugs. Output ONLY valid JSON."
        )
        self.reset_history()
        raw = self.generate_response(prompt)
        return self._parse_report(raw)

    def analyze_raw(self, file_contents: str) -> dict:
        """Naive mode: analyze from raw file content only — no graph, no Obsidian.

        Used for the token-efficiency baseline comparison. Every file is sent in full;
        there is no pre-filtering or graph-guided targeting.
        """
        prompt = (
            "Analyze this Python codebase for architectural bugs. "
            "All source files are provided below — no knowledge graph is available.\n\n"
            f"Source Files:\n{file_contents}\n\n"
            "Identify all architectural bugs. Output ONLY valid JSON."
        )
        self.reset_history()
        raw = self.generate_response(prompt)
        return self._parse_report(raw)

    def _collect_snippets(self, kg: KnowledgeGraph, source_root: str) -> str:
        """Extract code snippets for the top-5 most central nodes (token-efficient)."""
        snippets: list[str] = []
        m = kg.metrics
        for node_id, _ in m.top_hubs[:5]:
            node = kg.get_node(node_id)
            if not node:
                continue
            try:
                lines = Path(node.file_path).read_text(encoding="utf-8").splitlines()
                start = max(0, node.line_start - 1)
                end = min(len(lines), node.line_end)
                code = "\n".join(lines[start:end])[:800]   # cap at 800 chars per snippet
                header = f"### {node.label} ({node.file_path}:{node.line_start})"
                snippets.append(f"{header}\n```python\n{code}\n```")
            except OSError:
                pass
        return "\n\n".join(snippets)

    def _parse_report(self, raw: str) -> dict:
        """Parse the LLM response into a structured report dict."""
        text = self._strip_fences(raw)
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            return {"bugs": [], "summary": raw[:300], "parse_error": True}
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            return {"bugs": [], "summary": raw[:300], "parse_error": True}

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Remove markdown code fences (```…```) from LLM output."""
        t = text.strip()
        if t.startswith("```"):
            lines = t.split("\n")
            inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            return "\n".join(inner).strip()
        return t
