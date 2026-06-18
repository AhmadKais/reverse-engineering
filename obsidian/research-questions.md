# Research Questions & Answers

Answering the required research questions from Assignment 04, Section 4.

---

## Q1 — What was the actual architecture, and what wasn't obvious at first glance?

**Actual architecture**:

```
polygons/polygons.py
 ├── class Polygon(object)         ← OOP design
 │    └── __init__(sides, sum, angle)
 ├── calc_polygon_details(sides)   ← factory function
 └── draw_polygon(polygon_details) ← renderer

mathsquiz/mathsquiz.py
 └── [flat procedural God Script]
      ├── 6 questions inline
      └── final score block
```

**Not obvious at first**: The graph showed 9 nodes and 0 edges, with `polygons.py` and `mathsquiz.py` producing no nodes at all. The architecture above was completely invisible to the graph — it had to be reverse-engineered from raw file text by the `raw_reader` node. The Polygon class, factory function, and renderer were only discovered after the agents read raw source.

**Surprise**: The `mathsquiz-step2.py` and `mathsquiz-step3.py` files show exactly how `mathsquiz.py` *should* look after proper refactoring — these step files were the intended future state, not the current state.

---

## Q2 — Which components are most central in the system?

In the broken state: **none** — all betweenness centrality scores are 0.0000. The graph has 0 edges, so no node bridges paths between other nodes.

In the fixed state (after applying patches to `artifacts/`):
- `calc_polygon_details` becomes central — it creates the Polygon object and is called by any consumer of polygon data
- `Polygon.__init__` becomes the entry point for all OOP usage
- The quiz God Script has no central node even after fixing — it remains procedural

---

## Q3 — Where are the "God Nodes" / mixed responsibilities?

`mathsquiz/mathsquiz.py` is a **God Script** — the entire quiz logic lives in a single top-level file with no functions:
- Greets the user
- Asks 6 questions
- Validates answers
- Tracks score
- Prints result

All of this is inline, in order, with no decomposition. The step files (`mathsquiz-step1/2/3.py`) show the intended decomposition:
- `welcome_message()` → greeting
- `ask_question(question, answer)` → one question
- `print_final_scores(score)` → result

**How the graph revealed it**: The step files produced parseable nodes (3 functions each). The main `mathsquiz.py` produced 0 — because inline code is not visible to AST parsing at the function/class level; only flat script.

---

## Q4 — How to extract OOP and block schemas from buggy code?

**Method**:
1. Run AST parser → note which entities it extracts (even partially)
2. Read raw file text for files that failed parsing
3. Identify intended class/function boundaries from indentation and naming, even with syntax errors
4. Apply: what *would* the class hierarchy be if syntax were valid?

**OOP schema** (see `reports/OOP_SCHEMA.md`):
```
Polygon
 └── __init__(sides, internal_angles_sum, internal_angle)
      └── called by: calc_polygon_details()
           └── used by: draw_polygon()
```

**Block schema** (see `reports/BLOCK_SCHEMA.md`):
```
[Input: sides] → calc_polygon_details → [Polygon object]
                                              ↓
                                       draw_polygon
                                              ↓
                                     [terminal output]
```

The bugs (`Object` instead of `object`, `new` keyword) actually *helped* identify the developer's mental model — Java/JavaScript OOP mapped incorrectly onto Python.

---

## Q5 — How did you identify the bug, and what led you there?

**Path to root cause**:

1. **Graph signal**: 0 edges → `is_sparse=True` → `raw_reader` branch
2. **raw_reader** read both buggy files and described their structure
3. **AnalyzerAgent** received the description + file snippets → identified 16 bugs with line evidence
4. **Root cause for polygons.py**: Java/JavaScript developer background — `new` keyword and `Object` base class are Java patterns
5. **Root cause for mathsquiz.py**: Python 2 code never migrated, with arithmetic errors added on top

The graph cost 0 tokens to reveal the investigation target. No manual file reading was needed to determine which files to focus on.

---

## Q6 — What was the advantage of graph-guided navigation vs. linear file reading?

| Dimension | Linear reading | Graph-guided |
|---|---|---|
| Files sent to LLM | All 5 | 2 (only broken ones) |
| Step files in context | Yes (wasted) | No — excluded by graph signal |
| Pre-analysis needed | None | 0 tokens (graph is local) |
| "Lost in the Middle" risk | High (5 files mixed) | Low (2 focused files) |
| Structural insight before LLM call | None | "0 edges = broken language-level" |

The graph acts as a **zero-cost pre-filter**: it determined in 0 tokens which 2 of 5 files contained the bugs. The 3 step-files (≈1,622 tokens) never wasted any LLM context.

---

## Q7 — How did the graph-guided agent save tokens?

**Context compression mechanisms used**:

1. **Sparse-graph detection** (`SPARSE_EDGE_THRESHOLD = 5`): if `edge_count < 5`, skip the NavigatorAgent entirely. The navigator reads graph topology — useless when the graph has no edges.

2. **Targeted file selection**: the `raw_reader` node reads only files that **failed AST parsing** (0 nodes). Step files that parsed cleanly are excluded.

3. **Structured intermediate state**: each LangGraph node receives only what the previous node produced — not the full source. The AnalyzerAgent receives raw_reader's description + targeted snippets, not all 5 files.

4. **Token budget guardrail** (`AgentBudget`): shared across all 3 agents, raises `TokenBudgetExceededError` if exceeded. Prevents runaway iterations.

**Result**: 15,805 / 40,000 tokens used (39% of budget). 16 bugs found in 1 pass.

---

## Q8 — What extensions or improvements would you add?

1. **Dynamic hot.md from git diff**: parse `git diff` to see which files changed recently → add them to hot.md as high-priority suspects automatically
2. **Centrality-ranked suspect list**: rank nodes by proximity to 0-edge boundary for targeted investigation
3. **Orphan component detection**: automatically flag modules with 0 in-edges and 0 out-edges as candidates for dead code review
4. **Multi-iteration improvement loop**: run `analyze → fix → rebuild graph → compare metrics` across N iterations (already implemented in `sdk.py` with `--improve`)
5. **Mixed-responsibility detector**: flag any function/class where betweenness > threshold AND in-degree > threshold as a potential God Node needing refactoring

See `README.md` Section 11 for implemented extensions.

---

*Navigation*: [[index]] · [[hot]] · [[investigation]] · [[BEFORE_AFTER]]
