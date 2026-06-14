# PRD — EX04: Reverse Engineering with AI Agents

**Product**: Token-efficient codebase reverse-engineering pipeline  
**Author**: Ahmad Khalil  
**Course**: AI Orchestration — Lecture 07  
**Status**: Delivered

---

## Problem Statement

Reading an unfamiliar codebase from scratch is slow and expensive — especially with LLMs. A naive approach (dump all files into context) wastes tokens on irrelevant code, risks truncation on large repos, and gives no structural insight before diving into details.

**This project solves that** by building a graph-guided reading strategy: parse the codebase into a knowledge graph first, rank nodes by centrality, then send only the most important 5 snippets to the LLM — not the whole repo.

---

## Goals

1. Parse any Python codebase into a navigable knowledge graph without manual inspection
2. Export that graph as an Obsidian vault (human-readable + machine-readable)
3. Automatically identify architectural bugs using graph topology + targeted code snippets
4. Propose concrete fixes for every bug found
5. Do all of this within a hard token budget

---

## Non-Goals

- Does not support non-Python codebases
- Does not automatically apply fixes to disk (proposals only)
- Does not replace human code review
- Does not require internet access beyond the Anthropic API

---

## Functional Requirements

### FR-1: Graph Builder
- Parse all `.py` files in a directory tree using Python's `ast` module
- Extract nodes: `MODULE`, `CLASS`, `FUNCTION`, `METHOD`
- Extract edges: `imports`, `inherits`, `calls`, `composes`
- Infer composition edges from `__init__` constructor arguments
- Skip `__pycache__` and non-`.py` files
- Handle syntax errors gracefully (return empty lists, not crash)

### FR-2: Graph Metrics
- Compute betweenness centrality for all nodes
- Detect bridge edges (removal disconnects the graph → SPOF candidates)
- Detect communities via greedy modularity
- Rank top-10 hubs by betweenness
- Expose in/out degree for every node

### FR-3: Obsidian Vault Export
- `graph.json` — full node/edge data with metrics
- `hot.md` — ranked hub table with wiki-links
- `index.md` — all nodes grouped by kind
- `nodes/*.md` — one note per node with incoming/outgoing relationship wiki-links

### FR-4: LangGraph Workflow
- `build_graph` node: parse → build → export vault
- `navigate` node (dense path): graph summary → architectural overview
- `raw_reader` node (sparse path): raw file text → structural description
- `analyze` node: description + snippets → structured bug report (JSON)
- `fix` node: bug report + code → fix proposals (JSON)
- Conditional routing: sparse if `edge_count < 5`, dense otherwise
- Error propagation: any node failure sets `state["error"]`; all downstream nodes skip

### FR-5: Token Budget
- Single `AgentBudget` shared across all agents
- Hard ceiling: raises `TokenBudgetExceededError` when exceeded
- Budget configurable via `--budget N` CLI flag
- Token usage reported in final output

### FR-6: Agent Output
- All agents output raw JSON (no markdown fences)
- 3-stage parsing: strip fences → `json.loads` → embedded scan
- On parse failure: `parse_error: True` flag (never silent)
- Fallback bug report built from `raw_reader` text if Analyzer returns unparseable JSON

### FR-7: CLI Modes
| Flag | Behavior |
|------|----------|
| *(none)* | Full pipeline (requires API key) |
| `--graph-only` | Build + export vault, no LLM calls |
| `--improve` | Multi-pass loop: analyze → fix → re-analyze |
| `--diagram` | Print LangGraph Mermaid diagram and exit |
| `--budget N` | Set token ceiling (default: 60,000) |
| `--source PATH` | Override target codebase path |

---

## Non-Functional Requirements

### NFR-1: Token efficiency
- Navigator receives a compact JSON summary (~350 tokens), not raw files
- Analyzer reads only top-5 hub snippets (800 chars each)
- Full pipeline must complete within 30% of a 50,000-token budget on `broken-python`

### NFR-2: Resilience
- Syntax errors in target code must not crash the pipeline (sparse fallback)
- API rate-limit errors must retry with backoff (max 2 retries)
- Missing API key must trigger `--graph-only` mode automatically with a warning

### NFR-3: Reproducibility
- Graph export must be deterministic for the same input
- `analysis_report.json` must be JSON-serializable (no raw Python objects)

### NFR-4: Test coverage
- All logic units testable without real API calls (mock `anthropic.Anthropic`)
- ≥ 100 tests across graph builder, agents, workflow, and integration layers
- Coverage target: 80% of `src/`

---

## User Stories

**As a student** reverse-engineering an unfamiliar repo, I want to open the Obsidian vault and immediately see which classes are most central, so I know where to start reading.

**As a student** whose target code has syntax errors, I want the pipeline to still find bugs instead of crashing, so I don't have to fix the code manually before analyzing it.

**As a student** with limited API credits, I want a hard token budget enforced across all agents, so I never accidentally blow my quota on one run.

**As a grader** reviewing the assignment, I want a single `uv run python main.py --budget 40000` command that produces a complete bug report and Obsidian vault, so I can evaluate the submission without setup.

---

## Success Metrics

| Metric | Target | Achieved |
|--------|--------|----------|
| Bugs found in `broken-python` | ≥ 10 | 12 (16 with agent) |
| Token usage on full run | < 20,000 | ~15,022 |
| Test count | ≥ 50 | 101 |
| Vault exported files | graph.json + hot.md + index.md + nodes/ | ✅ |
| Pipeline completes on sparse graph | No crash | ✅ |
| Pipeline completes without API key | Graph-only mode | ✅ |

---

## Constraints

- Python 3.12+
- Anthropic API only (no OpenAI, no local models)
- `uv` for dependency management
- Target codebase must be one of the three approved repos from the EX04 PDF
- Fixed files written to `artifacts/`, not overwriting originals

---

## Out of Scope (future)

- Auto-apply fixes to disk (currently proposals only)
- Support for JavaScript/TypeScript codebases
- GUI or web interface
- Streaming LLM output
- Multi-repo comparison
