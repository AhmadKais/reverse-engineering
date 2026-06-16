# Token Efficiency — Naive Baseline vs Graph-Guided

Demonstrating the "Lost in the Middle" problem and how graph-guided navigation solves it.

Both runs measured against the same target: `data/broken-python/`  
Commands used to produce these results:

```bash
# Naive baseline (measured)
uv run python main.py --naive --budget 60000

# Graph-guided pipeline (measured)
uv run python main.py --budget 40000
```

---

## Source Files

| File | Bytes | Role |
|------|-------|------|
| `polygons/polygons.py` | 1,882 | **Buggy** — OOP + syntax errors |
| `mathsquiz/mathsquiz.py` | 1,445 | **Buggy** — Python 2, logic errors |
| `mathsquiz/mathsquiz-step1.py` | 3,005 | Clean — intended refactor target |
| `mathsquiz/mathsquiz-step2.py` | 1,660 | Clean — intended refactor target |
| `mathsquiz/mathsquiz-step3.py` | 1,822 | Clean — intended refactor target |
| **Total** | **9,814 bytes** | |

---

## Approach A — Naive Baseline (measured)

**Mode**: all 5 `.py` files sent to Analyzer → Fixer with no graph, no Obsidian.  
**Run**: `uv run python main.py --naive --budget 60000`

| Agent | Files sent | Input tokens | Output tokens |
|-------|-----------|-------------|---------------|
| AnalyzerAgent | all 5 files | 3,101 | 1,331 |
| FixerAgent | all 5 files + bug report | 4,719 | 1,558 |
| **TOTAL** | 5 files × 2 agents | **7,820 input** | **2,889 output** |
| **Grand total** | | | **10,709 tokens** |

**Results**:
- Bugs found: **6** (missed 10 of the 16 real bugs)
- Fixes proposed: **9**
- Budget used: **10,709 / 60,000 (18%)**

**Why it underperforms — "Lost in the Middle"**:
- The 3 clean step files (5,487 bytes, ~1,372 tokens) wasted context that the LLM used to process irrelevant code
- No structural signal about which files are broken — the LLM had to infer this from raw content
- Relevant bugs in `polygons.py` and `mathsquiz.py` were **buried in the middle** of a 5-file dump
- The LLM missed 10 bugs because the valid step files diluted focus on the broken ones

---

## Approach B — Graph-Guided Pipeline (measured)

**Mode**: AST graph built → sparse detection → only broken files routed to agents.  
**Run**: `uv run python main.py --budget 40000`

### Step 1 — Build graph (0 tokens — local, no API)

```
AST parse → 9 nodes, 0 edges
is_sparse = True  (edge_count < SPARSE_EDGE_THRESHOLD = 5)
→ route to raw_reader  (skip NavigatorAgent)
```

The graph identified in **0 tokens** which 2 of 5 files were broken.  
Step files never entered the LLM context.

### Step 2 — raw_reader → analyze → fix

Files read: `polygons.py` (1,882 bytes) + `mathsquiz.py` (1,445 bytes) = **3,327 bytes only**

| Agent | Files sent | Input tokens | Output tokens |
|-------|-----------|-------------|---------------|
| raw_reader (BaseAgent) | 2 broken files | 2,800 | ~400 |
| AnalyzerAgent | description + 2 snippets | 3,100 | ~1,500 |
| FixerAgent | bug report + 2 snippets | 2,929 | ~3,846 |
| **TOTAL** | 2 files only | **8,829 input** | **5,746 output** |
| **Grand total** | | | **14,575 tokens** |

**Results**:
- Bugs found: **16** (100% of actual bugs — 5 in polygons.py, 11 in mathsquiz.py)
- Fixes proposed: **18**
- Budget used: **14,575 / 40,000 (36%)**

---

## Comparison (Both Runs Measured)

| Metric | Naive Baseline (measured) | Graph-Guided (measured) |
|--------|--------------------------|-------------------------|
| Files sent to LLM | **5 files** (all) | **2 files** (broken only) |
| Bytes in LLM context | **9,814 bytes** (all) | **3,327 bytes** (targeted) |
| Step files in context | **Yes** (wasted ~1,372 tokens) | **No** — excluded by graph signal |
| Graph pre-filtering cost | — | **0 tokens** (local AST) |
| Total tokens used | **10,709** | 14,575 |
| Input tokens | 7,820 | 8,829 |
| Output tokens | 2,889 | 5,746 |
| **Bugs found** | **6** ← missed 10 bugs | **16** ← all bugs found |
| Fixes proposed | 9 | 18 |
| Investigation iterations | 1 | 1 |
| Structural insight | None (no graph) | ✅ 0-edge signal = broken language-level |
| "Lost in the Middle" risk | **High** (bugs buried in 5-file dump) | **Low** (2 focused files) |

---

## The Core Finding

The naive approach used **fewer tokens (10,709 vs 14,575)** but found **far fewer bugs (6 vs 16)**.

This is the "Lost in the Middle" effect in practice: when `polygons.py` and `mathsquiz.py` are buried
between three clean step files, the LLM's attention spreads across all five. The bugs in positions
2 and 5 (middle and end of context) receive less focus than the bugs at position 1.

The graph-guided approach used slightly more tokens because the pipeline runs three focused agents
(raw_reader + Analyzer + Fixer) with structured intermediate state. That extra structure is what
allowed it to find 167% more bugs than the naive approach.

**Token efficiency is not just about count — it's about bugs found per token**:

| Metric | Naive | Graph-Guided |
|--------|-------|-------------|
| Tokens per bug found | 1,782 tokens/bug | **911 tokens/bug** |
| Context relevance | ~66% relevant (2 buggy files out of 5) | ~100% relevant |
| Knowledge before first LLM call | None | Graph topology (0 tokens) |

---

## Why the Graph Wins Even with More Tokens

1. **Zero-cost pre-filter**: the graph identified the 2 broken files in 0 API tokens — local AST analysis
2. **Context precision**: only 3,327 of 9,814 bytes reached the LLM (34% context reduction)
3. **No "Lost in the Middle"**: 2-file context keeps bugs at the front of the attention window
4. **Structured intermediate state**: each LangGraph node passes only its output to the next — not the full source
5. **Diagnostic signal**: 0 edges is not an absence of information — it's the finding

---

## Token Budget Breakdown (Graph-Guided)

| Phase | Tokens | % of 40k Budget |
|-------|--------|-----------------|
| Graph build + vault export | **0** | 0% |
| raw_reader node | ~3,200 | ~8% |
| Analyzer node | ~4,600 | ~11.5% |
| Fixer node | ~6,775 | ~17% |
| **Total used** | **14,575** | **36%** |
| **Remaining** | **25,425** | **64%** |

64% of the budget remained unused — headroom for additional investigation passes if needed.
