# Prompt Engineering Log (ספר הפרומפטים)

Development log of all AI-assisted prompts used during EX04.  
Tool: Claude Code (claude-sonnet-4-6) via Anthropic API.

---

## Phase 1 — Architecture Design

**Goal**: Design the LangGraph StateGraph with adaptive routing

**Prompt**:
> Design a LangGraph StateGraph that reverse-engineers a Python codebase.
> It should: (1) parse .py files to a networkx DiGraph using AST, (2) export an Obsidian vault,
> (3) route through Navigator → Analyzer → Fixer agents.
> Add an adaptive fallback: if edge_count < 5 (broken/Python-2 code), skip Navigate and use a raw_reader instead.
> Token budget must be enforced via a shared AgentBudget object.

**Result**: 5-node StateGraph design:
`build_graph → (navigate | raw_reader) → analyze → fix`
with `is_sparse` conditional edge at `SPARSE_EDGE_THRESHOLD = 5`.

---

## Phase 2 — AST Parser Design

**Goal**: Parse Python files to GraphNode + GraphEdge lists

**Prompt**:
> Write an AST-based parser for Python files that extracts:
> - Module, Class, Function nodes (as GraphNode Pydantic models with NodeKind enum)
> - Import, Call, Inheritance edges (as GraphEdge Pydantic models with EdgeKind enum)
> Use ast.NodeVisitor. Handle SyntaxError gracefully (return empty lists, not exception).
> Each GraphNode needs: id, name, kind, file_path, line_number, docstring, source_snippet.

**Result**: `src/graph_builder/ast_parser.py` + `ast_visitors.py` with full SyntaxError fallback.

---

## Phase 3 — Obsidian Vault Exporter

**Goal**: Export knowledge graph to Obsidian-compatible markdown vault

**Prompt**:
> Write an Obsidian vault exporter for a networkx DiGraph.
> Output: hot.md (top-10 nodes by betweenness centrality), index.md (all nodes table),
> nodes/<id>.md (one page per node with metadata + wikilinks), graph.json (for visualization),
> graph.html (interactive D3.js force graph).
> Nodes should link to each other using Obsidian [[wikilink]] syntax.

**Result**: `src/graph_builder/obsidian_exporter.py`, `vault_writers.py`, `note_renderer.py`, `graph_html_writer.py`.

---

## Phase 4 — Agent System Prompt Design

**Goal**: Design system prompts for Navigator, Analyzer, and Fixer agents

### NavigatorAgent System Prompt

**Prompt**:
> Write a system prompt for a NavigatorAgent that reads a knowledge graph summary
> (nodes, edges, centrality scores) and produces a 3-paragraph architectural overview:
> (1) most important components, (2) how they connect, (3) suspected problem areas.
> Output must be plain text, no markdown headers.

**Result**: NavigatorAgent system prompt in `src/agents/navigator_agent.py`.

### AnalyzerAgent System Prompt

**Prompt**:
> Write a system prompt for an AnalyzerAgent that receives:
> - A graph summary (node list, centrality rankings)
> - Raw source code snippets of the 2 most important files
> It must output a JSON array of bugs. Each bug: file, function, bug_type, severity, evidence, fix.
> Output raw JSON only — no markdown fences. If no bugs found, output {"bugs": []}.

**Result**: AnalyzerAgent system prompt + 3-stage JSON parser in `src/agents/analyzer_agent.py`.

### FixerAgent System Prompt

**Prompt**:
> Write a system prompt for a FixerAgent that receives a structured bug report JSON
> and outputs a fix plan JSON: array of fixes with fields:
> file, scope, category, description, corrected_code.
> CRITICAL: Do NOT include actual Python code inside JSON string values — describe the fix in plain English.
> This avoids JSON escaping bugs. Output raw JSON only.

**Result**: FixerAgent system prompt + fix parser in `src/agents/fixer_agent.py` + `fixer_parsers.py`.

---

## Phase 5 — LangGraph Workflow Nodes

**Goal**: Wire all nodes into the StateGraph with error propagation

**Prompt**:
> Wire these 5 nodes into a LangGraph StateGraph:
> build_graph (AST parse + vault export), navigate (dense path), raw_reader (sparse fallback),
> analyze (bug detection), fix (fix proposals).
> Each node must check state["error"] first and skip if set.
> The conditional edge after build_graph checks state["is_sparse"].
> Use WorkflowState TypedDict with fields: source_root, vault_dir, knowledge_graph,
> graph_summary, raw_files, navigation, bug_report, fix_report, token_usage, is_sparse, error.

**Result**: `src/langgraph_workflow.py`, `src/workflow_nodes.py`, `src/workflow_helpers.py`, `src/workflow_state.py`.

---

## Phase 6 — SDK Layer

**Goal**: Wrap the workflow in an SDK for multi-pass improvement loops

**Prompt**:
> Create an SDK class wrapping run_workflow() for multi-pass analysis.
> Method: improve(iterations=N) — runs the pipeline N times, each time passing the previous
> bug report back as context. Track token usage across iterations.
> Save improvement_history.json to artifacts/ (not vault).

**Result**: `src/sdk.py` with `GraphifySDK.improve()` method.

---

## Phase 7 — Test Suite Design

**Goal**: Design 104 tests covering all modules

**Prompt**:
> Write pytest tests for:
> - KnowledgeGraph (graph_builder): add_node, add_edge, centrality, summary, sparse detection
> - AST parser: parse valid Python, parse SyntaxError file, parse directory
> - AgentBudget: record(), exceeded check, TokenBudgetExceededError
> - AnalyzerAgent / FixerAgent: mock Anthropic API, test JSON parsing stages, edge cases
> - LangGraph workflow: node wiring, error skip behavior, routing logic
> - Obsidian exporter: file creation, graph.json content, graph.html generation
> All agent tests must mock anthropic.Anthropic — no real API calls.

**Result**: 13 test files, 104 tests in `tests/`.

---

## Phase 8 — Debugging & Refinement

**Prompt used to debug vault pollution**:
> The analysis_report.json and improvement_history.json are being saved inside obsidian/
> (the vault directory). Fix all three entry points (runner_pipeline.py, runner_improve.py, sdk.py)
> to save them to artifacts/ instead.

**Result**: Fixed all three files to use `Path(vault_dir).parent / "artifacts"`.

**Prompt used to fix raw_reader scope**:
> raw_reader_node sends ALL 5 files including step files to the LLM.
> The step files (step2.py, step3.py, step3-solved.py) are known-good scaffolding files,
> not the buggy targets. Fix raw_reader to exclude files with "step" in the name,
> matching the existing _analyze_raw() filter.

**Result**: Added step-file filter in `src/workflow_nodes.py:raw_reader_node`.

---

## Summary Statistics

| Phase | Prompts | Files Created |
|---|---|---|
| Architecture design | 1 | StateGraph design |
| AST parser | 1 | 2 files |
| Obsidian exporter | 1 | 4 files |
| Agent prompts | 3 | 4 files |
| LangGraph nodes | 1 | 4 files |
| SDK layer | 1 | 1 file |
| Test suite | 1 | 13 files |
| Debug/refine | 5 | multiple fixes |
| **Total** | **14** | **30+ files** |
