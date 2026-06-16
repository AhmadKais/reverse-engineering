# GRAPH_REPORT.md — Knowledge Graph Analysis

**Target**: `data/broken-python/` (martinpeck/broken-python)  
**Graph Builder**: Custom AST-based Grphify equivalent (`src/graph_builder/`)  
**Vault**: `obsidian/`

---

## Graph Statistics

| Metric | Value | Interpretation |
|---|---|---|
| Nodes | 9 | Only step files parsed — main files have syntax errors |
| Edges | 0 | **Key finding**: 0 edges = files cannot be loaded by Python 3 AST |
| Communities | 9 | Each node is its own isolated community (no connections) |
| Bridge edges | 0 | No bridges — graph is fully disconnected |
| Parseable files | 3 / 5 | `mathsquiz.py` and `polygons.py` fail AST parsing |

## Node Breakdown by Kind

| Kind | Count | Notes |
|---|---|---|
| Module | 3 | `mathsquiz-step1`, `step2`, `step3` |
| Function | 6 | `welcome_message`, `ask_question`, `print_final_scores` × 2 step files |
| Class | 0 | `Polygon` class unparseable (syntax error in `polygons.py`) |

## Why 0 Edges Is the Finding

A normally structured Python project of this size would have 20–50 edges (imports, function calls, inheritance). Zero edges means **every import and call relationship is invisible** to the AST — because the files that contain them (`mathsquiz.py`, `polygons.py`) fail to parse.

This triggered the **sparse-graph conditional branch** in the LangGraph workflow:

```
build_graph (9 nodes, 0 edges)
    └── is_sparse = True  ←  threshold: < 5 edges
         └── raw_reader node reads files directly
              └── analyze + fix on raw text
```

## Centrality: All Nodes at Zero

| Rank | Node | Kind | Betweenness | In | Out |
|---|---|---|---|---|---|
| 1–9 | all nodes | module/function | 0.0000 | 0 | 0 |

All centrality = 0 because the graph has no edges. This is itself diagnostic information: the graph is not "boring" — it is **screaming that something is wrong**.

## Before vs After Fix (Graph Comparison)

| Metric | Before fix (buggy files) | After fix (corrected files) |
|---|---|---|
| Parseable files | 3/5 | 5/5 |
| Nodes | 9 | 17 |
| Edges | 0 | 9 |
| Polygon class visible | No | Yes |
| `calc_polygon_details` visible | No | Yes |

Running `uv run python main.py --graph-only --source artifacts/` after applying fixes produces a richer graph with the `Polygon` class, its methods, and function call edges now visible.

## Architectural Insight

The sparse graph confirmed in 3 seconds what would take 10 minutes of manual reading: **both main files are broken at the language level**. The step files (`step2.py`, `step3.py`) parsed correctly and revealed the *intended* architecture — 3 well-named functions (`welcome_message`, `ask_question`, `print_final_scores`) that the God Script should be refactored into.
