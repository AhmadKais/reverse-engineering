"""Public SDK facade — orchestrates the full reverse-engineering pipeline.

Pipeline:
  1. GraphBuilder — AST-parse the target codebase → KnowledgeGraph
  2. ObsidianExporter — export vault files (graph.json, index.md, hot.md, node notes)
  3. NavigatorAgent — architectural overview from graph topology
  4. AnalyzerAgent — identify architectural bugs
  5. FixerAgent — propose (and optionally apply) patches
  6. Improvement Loop — rebuild graph after each patch round, validate improvement

Implemented directly with the Anthropic SDK and a shared token budget.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from src.agents.analyzer_agent import AnalyzerAgent
from src.agents.base_agent import AgentBudget
from src.agents.fixer_agent import FixerAgent
from src.agents.navigator_agent import NavigatorAgent
from src.graph_builder.ast_parser import parse_directory
from src.graph_builder.graph_generator import KnowledgeGraph
from src.graph_builder.obsidian_exporter import ObsidianExporter


class ReverseEngineerSDK:
    """Orchestrates graph building + multi-agent reverse engineering analysis."""

    def __init__(
        self,
        vault_dir: str = "vault",
        token_budget: int = 60_000,
        improvement_iterations: int = 1,
    ) -> None:
        self.vault_dir = vault_dir
        self.improvement_iterations = improvement_iterations
        self.budget = AgentBudget(max_tokens=token_budget)
        self._navigator = NavigatorAgent(self.budget)
        self._analyzer = AnalyzerAgent(self.budget)
        self._fixer = FixerAgent(self.budget)

    # ------------------------------------------------------------------

    def analyze(self, source_root: str) -> dict:
        """Run the full pipeline once (no improvement loop).

        Returns a report dict with keys:
          graph_metrics, navigation, bugs, fixes, token_usage
        """
        print(f"[SDK] Parsing codebase: {source_root}")
        kg = self._build_graph(source_root)

        print(f"[SDK] Graph: {kg.metrics.node_count} nodes, {kg.metrics.edge_count} edges")
        self._export_vault(kg, source_dir=source_root)

        print("[SDK] Navigator: mapping architecture...")
        navigation = self._navigator.navigate(kg)

        print("[SDK] Analyzer: identifying architectural bugs...")
        bug_report = self._analyzer.analyze(kg, source_root)

        print("[SDK] Fixer: generating refactoring patches...")
        fix_report = self._fixer.propose_fixes(bug_report, source_root)

        report = {
            "source_root": source_root,
            "graph_metrics": kg.summary_dict(),
            "navigation": navigation,
            "bugs": bug_report,
            "fixes": fix_report,
            "token_usage": self.budget.status(),
        }
        self._save_report(report)
        return report

    def improve(self, source_root: str, apply_patches: bool = False) -> list[dict]:
        """Run the improvement loop: analyze → fix → rebuild graph → re-analyze.

        Each iteration rebuilds the knowledge graph after applying patches,
        confirming that centrality scores improved (lower SPOF risk).
        """
        results: list[dict] = []
        for iteration in range(1, self.improvement_iterations + 1):
            print(f"\n[SDK] ===== Improvement Iteration {iteration}/{self.improvement_iterations} =====")
            report = self.analyze(source_root)

            if apply_patches:
                print(f"[SDK] Applying patches (iteration {iteration})...")
                patch_results = self._fixer.apply_fixes(report["fixes"], source_root, dry_run=False)
                report["applied_patches"] = patch_results
            else:
                dry_results = self._fixer.apply_fixes(report["fixes"], source_root, dry_run=True)
                report["dry_run_patches"] = dry_results

            results.append(report)

            if iteration < self.improvement_iterations:
                time.sleep(1)   # brief pause between iterations

        self._save_improvement_history(results)
        return results

    # ------------------------------------------------------------------

    def _build_graph(self, source_root: str) -> KnowledgeGraph:
        nodes, edges = parse_directory(source_root)
        kg = KnowledgeGraph()
        kg.build(nodes, edges)
        kg.compute_metrics()
        return kg

    def _export_vault(self, kg: KnowledgeGraph, source_dir: str = "") -> None:
        exporter = ObsidianExporter(self.vault_dir)
        exporter.export(kg, source_dir=source_dir)
        print(f"[SDK] Vault exported to: {self.vault_dir}/")

    def _save_report(self, report: dict) -> None:
        out = Path(self.vault_dir) / "analysis_report.json"
        serializable = self._make_serializable(report)
        out.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
        print(f"[SDK] Report saved: {out}")

    def _save_improvement_history(self, results: list[dict]) -> None:
        out = Path(self.vault_dir) / "improvement_history.json"
        serializable = [self._make_serializable(r) for r in results]
        out.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
        print(f"[SDK] Improvement history saved: {out}")

    def _make_serializable(self, obj) -> object:
        """Recursively convert non-serializable types (sets, etc.) for JSON output."""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._make_serializable(v) for v in obj]
        if isinstance(obj, set):
            return sorted(self._make_serializable(v) for v in obj)
        if isinstance(obj, tuple):
            return [self._make_serializable(v) for v in obj]
        return obj
