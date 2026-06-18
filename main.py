"""EX04 — Reverse Engineering, Debugging, and Token-Efficient Agentic AI.

Entry point: parses the broken-python codebase, builds a knowledge graph,
exports an Obsidian vault, then runs Navigator → Analyzer → Fixer agents
via a LangGraph StateGraph.

Modes:
  default        LangGraph pipeline (Navigator → Analyzer → Fixer)
  --graph-only   Build and export the Obsidian vault, no AI agents
  --improve      Improvement loop: analyze → fix proposals → re-analyze
  --diagram      Print the LangGraph Mermaid diagram and exit
"""

from __future__ import annotations

import argparse
import json
import logging
import logging.config
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

_LOG_CONFIG = Path(__file__).parent / "config" / "logging_config.json"


def _configure_logging() -> None:
    """Load logging settings from config/logging_config.json and apply via dictConfig."""
    if not _LOG_CONFIG.exists():
        return
    with _LOG_CONFIG.open() as fh:
        cfg = json.load(fh)
    log_cfg = cfg.get("logging", {})
    level = getattr(logging, log_cfg.get("level", "INFO"), logging.INFO)
    fmt = log_cfg.get("format", "[%(levelname)s] %(message)s")
    handlers_cfg = log_cfg.get("handlers", {})
    handlers: list[logging.Handler] = []
    if handlers_cfg.get("console", {}).get("enabled", True):
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(logging.Formatter(fmt))
        handlers.append(ch)
    file_cfg = handlers_cfg.get("file", {})
    if file_cfg.get("enabled", False):
        log_path = Path(file_cfg.get("path", "results/run.log"))
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh2 = logging.FileHandler(log_path)
        fh2.setLevel(getattr(logging, file_cfg.get("level", "DEBUG"), logging.DEBUG))
        fh2.setFormatter(logging.Formatter(fmt))
        handlers.append(fh2)
    logging.basicConfig(level=level, handlers=handlers, format=fmt)

TARGET_DEFAULT = str(Path(__file__).parent / "data" / "broken-python")
OBSIDIAN_DEFAULT = str(Path(__file__).parent / "obsidian")


def main() -> None:
    parser = argparse.ArgumentParser(description="EX04: Reverse Engineering with AI Agents (LangGraph)")
    parser.add_argument("--source", default=TARGET_DEFAULT,
                        help="Path to the Python codebase to analyse")
    parser.add_argument("--vault", default=OBSIDIAN_DEFAULT,
                        help="Output directory for the Obsidian vault (default: ./obsidian)")
    parser.add_argument("--budget", type=int, default=60_000,
                        help="Token budget across all agents (default: 60000)")
    parser.add_argument("--graph-only", action="store_true",
                        help="Build and export the graph without calling AI agents")
    parser.add_argument("--improve", action="store_true",
                        help="Run the improvement loop (multiple analysis passes)")
    parser.add_argument("--iterations", type=int, default=2,
                        help="Number of improvement iterations (default: 2)")
    parser.add_argument("--diagram", action="store_true",
                        help="Print the LangGraph Mermaid diagram and exit")
    parser.add_argument("--naive", action="store_true",
                        help="Run naive baseline: send ALL files to agents (no graph, no Obsidian)")
    args = parser.parse_args()
    load_dotenv()
    _configure_logging()

    from src.runner_graph import _run_graph_only, _run_naive
    from src.runner_improve import _run_improvement_loop
    from src.runner_pipeline import _run_langgraph

    source = args.source
    if not Path(source).exists():
        print(f"ERROR: source path does not exist: {source}")
        sys.exit(1)

    if args.diagram:
        from src.langgraph_workflow import print_workflow_diagram
        print_workflow_diagram()
        return

    if args.naive:
        _run_naive(source, args.budget)
        return

    if args.graph_only:
        _run_graph_only(source, args.vault)
        return

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not set — running graph-only mode")
        _run_graph_only(source, args.vault)
        return

    if args.improve:
        _run_improvement_loop(source, args.vault, args.budget, args.iterations)
    else:
        _run_langgraph(source, args.vault, args.budget)


if __name__ == "__main__":
    main()
