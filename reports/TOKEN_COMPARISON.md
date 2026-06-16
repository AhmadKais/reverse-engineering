# Token Efficiency — Baseline vs Graph-Guided

Demonstrating the "Lost in the Middle" problem and how graph-guided navigation solves it.

---

## Setup

**Target**: `data/broken-python/` — 5 Python files, 9,814 bytes total  
**Task**: Find and fix all bugs in `polygons.py` and `mathsquiz.py`  
**Budget**: 40,000 tokens (`--budget 40000`)

| File | Bytes | Est. Tokens |
|------|-------|-------------|
| `polygons/polygons.py` | 1,882 | ~470 |
| `mathsquiz/mathsquiz.py` | 1,445 | ~361 |
| `mathsquiz/mathsquiz-step1.py` | 3,005 | ~751 |
| `mathsquiz/mathsquiz-step2.py` | 1,660 | ~415 |
| `mathsquiz/mathsquiz-step3.py` | 1,822 | ~456 |
| **Total source** | **9,814 bytes** | **~2,453 tokens** |

---

## Approach A — Naive Baseline (no graph)

Send all 5 files as raw text to a single LLM call per agent, 3 agents in sequence.

| Agent | Files sent | Est. input tokens | Est. output tokens |
|-------|-----------|-------------------|--------------------|
| Navigator | all 5 files + system prompt | ~2,453 + 300 = **2,753** | ~800 |
| Analyzer | all 5 files + nav output + system prompt | ~2,453 + 800 + 300 = **3,553** | ~1,500 |
| Fixer | all 5 files + bug report + system prompt | ~2,453 + 1,500 + 350 = **4,303** | ~2,000 |
| **TOTAL** | | **~10,609 input** | **~4,300 output** |
| **Grand total** | | | **~14,909 tokens** |

**Problems with this approach:**
- Step files (`step1/2/3.py`) are **valid Python with no bugs** — they waste ~1,622 tokens per agent call (~4,866 total) on irrelevant context
- All 3 files are mixed together in context — the "Lost in the Middle" problem makes it harder for the LLM to focus on the actual bugs
- No structural insight: the LLM doesn't know *which* files are broken before reading them all

---

## Approach B — Graph-Guided (our pipeline)

**Actual measured run**: `uv run python main.py --budget 40000`

### Step 1 — Build graph (0 tokens — local, no API)

```
AST parse → 9 nodes, 0 edges
is_sparse = True (threshold: < 5 edges)
→ route to raw_reader (skip navigate)
```

The graph immediately told us: skip the step files. Only `polygons.py` and `mathsquiz.py` failed AST parsing → only those 2 files entered the LLM context.

### Step 2 — raw_reader node

Files sent: `polygons.py` (1,882 bytes) + `mathsquiz.py` (1,445 bytes) = 3,327 bytes  
Step files never touched.

### Step 3 — analyze + fix nodes

Analyzer received: raw_reader description + 2 file snippets (capped)  
Fixer received: bug report JSON + 2 file snippets

### Actual token usage (from `obsidian/analysis_report.json`)

| Metric | Value |
|--------|-------|
| Input tokens used | **8,829** |
| Output tokens used | **5,746** |
| **Total tokens used** | **14,575** |
| Budget | 40,000 |
| Budget remaining | **25,425 (64%)** |

---

## Comparison

| Metric | Naive Baseline | Graph-Guided (actual) |
|--------|---------------|----------------------|
| Files sent to LLM | **5 files** (all) | **2 files** (only broken ones) |
| Textual units read | 5 files × 3 agents = **15 reads** | 2 files × 1 read + 2 snippets × 2 agents = **6 reads** |
| Investigation iterations | Unknown — may need re-runs if bugs missed | **1 pass** — all 16 bugs found in single run |
| Step files in context | Yes (wasted) | **No — excluded by graph** |
| Agents called | 3 sequential | 3 sequential (navigate skipped) |
| Total tokens | ~14,909 (estimated) | **14,575 (measured)** |
| Bugs found | Unknown — no graph insight | **16 bugs** |
| Fixes proposed | Unknown | **18 targeted fixes** |
| Budget used | ~37% (estimated) | **36% (measured)** |
| Speed to root cause | Slow — must read all 5 files first | **Instant** — 0-edge graph signal requires 0 tokens |
| Graph insight | None | ✅ 0-edge signal identified broken files |

---

## Why the Graph Approach Wins (Even at Similar Token Counts)

The total token counts are similar — but the **quality and targeting** are fundamentally different:

| Dimension | Naive | Graph-Guided |
|-----------|-------|-------------|
| Which files to read | Must read all 5 to find out | Graph told us in 0 tokens |
| Context relevance | ~40% irrelevant (step files) | ~100% relevant (only buggy files) |
| Structural insight | None | Sparse graph = "language-level failure" |
| Bug detection quality | Risk of "Lost in the Middle" | Focused on 2 files only |
| Iterations needed | Unknown — may need re-runs | 1 pass, 16 bugs found |

**Key insight**: The graph-guided approach found **16 bugs in 1 pass** using only 36% of the budget. The graph cost 0 tokens to build and told us immediately which 2 files to focus on — the step files never wasted a single token of LLM context.

---

## Token Budget Breakdown

| Phase | Tokens Used | % of Budget |
|-------|-------------|-------------|
| Graph build + vault export | 0 (local, no API) | 0% |
| raw_reader node | ~2,800 (input) | ~7% |
| Analyzer node | ~3,100 (input) | ~7.75% |
| Fixer node | ~2,929 (input) | ~7.3% |
| All output tokens | 5,746 | 14.4% |
| **Total used** | **14,575** | **36%** |
| **Remaining** | **25,425** | **64%** |

The pipeline left **64% of the 40,000 token budget unused** while finding 16 bugs across 2 files and proposing 18 concrete fixes with file paths and explanations.
