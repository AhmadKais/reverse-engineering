# Investigation Log — broken-python

Systematic reverse-engineering trace using the Grphify graph + LangGraph agents.

---

## Step 1 — Build the Graph

```bash
uv run python main.py --graph-only
```

**Result**: 9 nodes, 0 edges, 9 communities, 0 bridges.

| Signal | Meaning |
|---|---|
| 9 nodes | Only 3 step-files parsed cleanly |
| 0 edges | No call/import relationships found |
| 9 communities | Every node is isolated — nothing connects |
| is_sparse = True | Threshold < 5 edges → sparse branch activated |

**Immediate conclusion**: Two files could not be parsed at all. The absence of nodes for `polygons.py` and `mathsquiz.py` is the finding.

---

## Step 2 — Read hot.md

Opened [[hot.md]] in Obsidian. All 9 visible nodes have `betweenness = 0.0000`.

A healthy project of this size would show at least one node with betweenness > 0 — a function that other functions call. Finding universal zero confirmed: **the graph is structurally empty because the source files are broken at the language level**.

---

## Step 3 — Route Decision (LangGraph)

```
build_graph node:
  graph.edge_count = 0
  is_sparse = True
  → conditional_edge → raw_reader   (NOT navigate)
```

The `navigate` node (NavigatorAgent) was skipped entirely — it reads graph topology, which is meaningless with 0 edges.

Instead, `raw_reader` (BaseAgent) was activated:
- Read `polygons/polygons.py` raw text (1,882 bytes)
- Read `mathsquiz/mathsquiz.py` raw text (1,445 bytes)
- Step files excluded — graph told us they were fine (they had parseable AST)

---

## Step 4 — Initial Suspects

Before running the full LLM pipeline, reviewing raw files manually against the graph signal:

**polygons.py** — the graph produced 0 nodes from this file. For a file that clearly intends to define a `Polygon` class, this means the class declaration itself is invalid.

Suspected root causes:
1. `class Polygon(Object)` — `Object` is not defined in Python; likely confused with Java
2. `new Polygon(...)` — `new` is not Python syntax

**mathsquiz.py** — similarly, 0 nodes. The file uses `print "..."` (Python 2 syntax) on first inspection.

Suspected root causes:
1. Python 2 print statements
2. Assignment `=` used in `if` conditions
3. Wrong answer values (eyeballing 8×7=55)

---

## Step 5 — Analyzer Agent Run

```
raw_reader output → AnalyzerAgent
```

AnalyzerAgent received:
- Raw description of both files from raw_reader
- Snippets of both files
- System prompt: identify all bugs with evidence

**Analyzer output** (16 bugs found):

### polygons.py (5 bugs)

| # | Bug | Line | Type |
|---|-----|------|------|
| 1 | `class Polygon(Object)` | ~1 | SyntaxError — NameError: Object |
| 2 | `poly = new Polygon(...)` | ~18 | SyntaxError — `new` not Python |
| 3 | `internal_angles_sum = 1000` hardcoded | ~13 | Logic — wrong for non-hexagon |
| 4 | `draw_polygon` loops 6×60° always | ~24 | Logic — hardcoded hexagon |
| 5 | Truncated `return` dict | ~20 | SyntaxError — incomplete |

### mathsquiz.py (11 bugs)

| # | Bug | Type |
|---|-----|------|
| 1 | `print "Hello!"` | SyntaxError — Python 2 |
| 2–7 | `if answer = 55` (×6) | SyntaxError — assignment in condition |
| 8 | All 6 answers wrong (8×7=55, etc.) | Logic |
| 9 | `score` never incremented | Logic |
| 10 | All questions print "Question 1:" | Logic |
| 11 | `else if` → must be `elif` | SyntaxError |

---

## Step 6 — Fixer Agent Run

```
bug report → FixerAgent
```

FixerAgent received the structured JSON bug report and produced 18 targeted fixes:
- 13 fixes for `mathsquiz.py`
- 5 fixes for `polygons.py` (including OOP refactor suggestion)

---

## Step 7 — Apply Fixes

Fixed files written to `artifacts/`:
- `artifacts/fixed_polygons.py` — parses under Python 3.12 ✅
- `artifacts/fixed_mathsquiz.py` — parses under Python 3.12 ✅

Graph rebuilt on fixed files → 6 nodes, 1 edge (see [[BEFORE_AFTER]]).

---

## Root Cause Summary

| File | Root Cause | Category |
|---|---|---|
| `polygons.py` | Developer with Java/JavaScript background wrote Python with wrong syntax (`Object`, `new`) | OOP misconception |
| `mathsquiz.py` | Python 2 code never migrated to Python 3; logic bugs added on top | Version mismatch + arithmetic errors |

---

## Token Efficiency

| Phase | Tokens | Insight |
|---|---|---|
| Graph build | 0 | Free — local AST analysis |
| raw_reader | ~2,800 | Only 2 buggy files read |
| analyze | ~3,100 | Focused on 2 files |
| fix | ~2,929 | Targeted proposals |
| **Total** | **15,805 / 40,000** | 39% of budget used |

The 3 step-files (3,005 + 1,660 + 1,822 = 6,487 bytes ≈ 1,622 tokens) **never entered the LLM context** — excluded by the graph signal alone.

See [[BEFORE_AFTER]] for full before/after comparison.
