# EX04 — Project Plan (Claude Reference Document)

## Project Identity

**Name**: Reverse Engineering with AI Agents (LangGraph + Graphify)  
**Assignment**: EX04, Lecture 07, AI Orchestration Course  
**Author**: Ahmad Khalil  
**Working directory**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW4`  
**Stack**: Python 3.12, LangGraph, Anthropic SDK, networkx, Pydantic, uv, pytest  

---

## Goal

Build a **token-efficient code reverse-engineering pipeline** that:
1. Parses a Python codebase into a knowledge graph (AST → networkx DiGraph)
2. Exports the graph as an Obsidian vault (graph.json, hot.md, node notes)
3. Routes the graph through a LangGraph StateGraph: Navigator → Analyzer → Fixer
4. Handles **sparse graphs** (syntax-broken code) via an adaptive fallback branch

**Target codebase**: `data/broken-python`

---

## Architecture

### Three-Layer Pipeline

```
[Source .py files]
      │
      ▼
[graph_builder/]       AST parsing → networkx DiGraph → Obsidian vault
      │
      ▼
[LangGraph StateGraph]
  build_graph ──(sparse?)──► raw_reader ──► analyze ──► fix
               ──(dense?)──► navigate  ──►

      │
      ▼
[analysis_report.json + obsidian/ vault]
```

### Module Map

| Module | Responsibility |
|--------|---------------|
| `src/graph_builder/ast_parser.py` | Walk `.py` files with `ast` module; emit `GraphNode` + `GraphEdge` lists |
| `src/graph_builder/graph_generator.py` | Build `networkx.DiGraph`; compute betweenness, bridges, communities |
| `src/graph_builder/obsidian_exporter.py` | Write `graph.json`, `hot.md`, `index.md`, `nodes/*.md` |
| `src/agents/base_agent.py` | `AgentBudget` + `BaseAgent` with retry and budget enforcement |
| `src/agents/navigator_agent.py` | Graph topology → architectural overview (dense path) |
| `src/agents/analyzer_agent.py` | Graph summary + code snippets → structured bug report |
| `src/agents/fixer_agent.py` | Bug report + code → fix proposals |
| `src/langgraph_workflow.py` | LangGraph `StateGraph`; wires nodes + conditional routing |
| `src/sdk.py` | Improvement loop wrapper |
| `main.py` | CLI entry point (`--graph-only`, `--improve`, `--diagram`) |

---

## Key Design Decisions

### 1. Sparse-Graph Fallback
When `edge_count < SPARSE_EDGE_THRESHOLD (5)`, the workflow routes to `raw_reader` instead of `navigate`. This handles codebases with syntax errors (Python 2 code, broken OOP) that block AST parsing. The `raw_reader` node reads raw file text and produces a structural description so the Analyzer still has meaningful context.

### 2. Token Budget Guardrail
`AgentBudget` is a shared counter passed to all three agents. Every `_call_llm()` call records actual `input_tokens + output_tokens` from the Anthropic response. When `total_used > max_tokens`, `TokenBudgetExceededError` is raised. This prevents runaway costs during the improvement loop.

### 3. Error Propagation via State
Each node checks `state.get("error")` first. If set, it returns immediately without calling the LLM. This means a failure in `build_graph` silently skips all downstream nodes — reported at the end, not mid-pipeline.

### 4. WorkflowState TypedDict
The `WorkflowState` flows through all nodes. Non-serialisable objects (`KnowledgeGraph`) are excluded when saving `analysis_report.json`. The `is_sparse` and `raw_files` fields are populated only by `build_graph_node`.

### 5. JSON-Only Agent Output
All three agents are instructed to output raw JSON with no markdown fences. `_parse_report` and `_parse_fixes` both do three-stage parsing: strip fences → `json.loads` → embedded scan. Fallback to `parse_error: True` so failures are visible.

---

## Data Flow (WorkflowState fields by node)

| Field | Set by | Read by |
|-------|--------|---------|
| `source_root` | initial | `build_graph`, `analyze` (file reads) |
| `vault_dir` | initial | `build_graph` (export) |
| `knowledge_graph` | `build_graph` | `navigate`, `analyze` |
| `graph_summary` | `build_graph` | summary print |
| `raw_files` | `build_graph` (sparse only) | `raw_reader`, `analyze`, `fix` |
| `is_sparse` | `build_graph` | routing, `analyze`, `fix` |
| `navigation` | `navigate` or `raw_reader` | logged |
| `bug_report` | `analyze` | `fix` |
| `fix_report` | `fix` | output |
| `token_usage` | every agent node | output |
| `error` | any node on exception | all downstream nodes |

---

## Entry Point Modes

```bash
uv run python main.py --graph-only          # No API key needed
uv run python main.py --budget 40000        # Full pipeline
uv run python main.py --improve --iterations 2 --budget 80000
uv run python main.py --diagram             # Print Mermaid
uv run pytest tests/ -v                     # Run all tests
```

---

## Test Coverage Map

| File | What it covers |
|------|---------------|
| `tests/test_graph_builder.py` | `ast_parser`, `KnowledgeGraph`, edge detection, line numbers |
| `tests/test_agents.py` | `AgentBudget`, `BaseAgent` (mocked), `AnalyzerAgent._parse_report`, `FixerAgent._parse_fixes` + `apply_fixes` |
| `tests/test_langgraph_workflow.py` | `build_workflow`, `build_graph_node`, error skip propagation |
| `tests/test_routing.py` | Routing, sparse detection, ObsidianExporter, data types, KG extras |
| `tests/test_routing.py` | Sparse/dense routing, `raw_reader_node`, `_fallback_bug_report`, `WorkflowState` helpers |

---

## Known Gaps / Future Work

- `NavigatorAgent.navigate()` has no unit test (requires mocked API)
- `ObsidianExporter` node-note content tested only in integration tests
- `sdk.py` `improve()` loop not unit-tested
- `_add_inferred_edges` composition inference has minimal coverage
- The `is_sparse` / `raw_files` fields are missing from `_initial_state()` helper in `test_langgraph_workflow.py` — must be added when writing new tests that set those fields

---

## Grading Checklist (EX04 PDF requirements)

- [x] Pick a repository from the approved list (`broken-python`)
- [x] Graph builder (Grphify equivalent) — AST → networkx
- [x] Obsidian vault export (graph.json, hot.md, index.md, node notes)
- [x] LangGraph StateGraph with ≥ 3 nodes
- [x] Navigator → Analyzer → Fixer agent chain
- [x] Adaptive routing (sparse fallback)
- [x] Token budget guardrail (`AgentBudget`)
- [x] Bug report with 12+ documented bugs
- [x] Fixed files in `artifacts/`
- [x] Reports: `OOP_SCHEMA.md`, `BLOCK_SCHEMA.md`, `BUG_REPORT.md`, `TOKEN_COMPARISON.md`
- [x] Tests (53 total)
- [ ] Screenshots in `artifacts/screenshots/` — must be added manually
