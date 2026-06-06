# Token Efficiency — Baseline vs Graph-Guided

Demonstrating the "Lost in the Middle" problem and how graph-guided navigation solves it.

---

## Setup

**Target**: `HW2/agent-debate/src/` — 83 nodes, ~1,800 lines of Python code  
**Task**: Find and explain the architectural bugs in the system

---

## Naive Baseline: Send Everything to the LLM

If we concatenated all Python files and sent them as context:

| File | Lines | Est. Tokens |
|---|---|---|
| `sdk.py` | 150 | ~600 |
| `agents/base_agent.py` | 149 | ~590 |
| `agents/debater_agent.py` | 30 | ~120 |
| `agents/judge_agent.py` | 120 | ~480 |
| `core/gatekeeper.py` | 108 | ~430 |
| `core/watchdog.py` | 65 | ~260 |
| `core/logger.py` | 70 | ~280 |
| `core/config.py` | 28 | ~110 |
| `data_types/message.py` | 45 | ~180 |
| `data_types/debate_result.py` | 35 | ~140 |
| `tools/search.py` | 25 | ~100 |
| `constants.py` | 10 | ~40 |
| System prompt (instruction) | — | ~300 |
| **TOTAL** | **~835 lines** | **~3,630 tokens** |

> This estimate is per agent call. With 3 agents × 1 call each = **~10,890 tokens** just for code context.  
> Plus the LLM's output tokens (~2,000 per agent) = **~16,890 total tokens**.

---

## Graph-Guided Approach: Read hot.md, Send Only Top Nodes

The Navigator reads the compact JSON summary (not the code):

```json
{
  "node_count": 83,
  "edge_count": 168,
  "top_hubs": [
    {"name": "DebateSDK.run",              "betweenness": 0.0443, "out_degree": 9},
    {"name": "BaseAgent.generate_response","betweenness": 0.0399, "in_degree": 5},
    {"name": "JudgeAgent",                 "betweenness": 0.0093},
    ...
  ]
}
```

The Analyzer then reads only the **top 5 hub code snippets** (capped at 800 chars each):

| What was sent | Tokens |
|---|---|
| Graph JSON summary | ~350 |
| Top-5 code snippets (×800 chars each) | ~1,000 |
| System prompt | ~300 |
| **Analyzer input total** | **~1,650** |

Fixer receives bug report + top-3 file snippets:

| What was sent | Tokens |
|---|---|
| Bug report JSON | ~500 |
| Top-3 affected files (×600 chars each) | ~600 |
| System prompt | ~350 |
| **Fixer input total** | **~1,450** |

---

## Measured Results (from analysis_report.json)

| Metric | Value |
|---|---|
| Navigator input tokens | ~1,200 |
| Analyzer input tokens | ~2,800 |
| Fixer input tokens | ~2,600 |
| **Total input tokens** | **~6,600** |
| Total output tokens | ~4,800 |
| **Grand total** | **~11,400 tokens** |

---

## Comparison

| Approach | Input Tokens | Output Tokens | Total | Reduction |
|---|---|---|---|---|
| Naive (all files) | ~10,890 | ~6,000 | ~16,890 | baseline |
| Graph-guided (hot nodes only) | ~6,600 | ~4,800 | **~11,400** | **−33%** |

---

## Why the Reduction Is Even Larger in Practice

The naive baseline assumes a single pass. In reality:
- A naive agent would need **multiple round-trips** to read all files
- Each round-trip re-sends the conversation history (context grows linearly)
- "Lost in the Middle" means the LLM ignores code placed in the middle of a long context — so bugs in `FIFOLogger._open_current` (a low-profile middle file) would be missed

The graph-guided approach **skips middle content entirely**: it reads only the nodes that the betweenness metric flags as critical. This means:
- Fewer tokens consumed
- Higher-quality bugs found (centrality = importance)
- No "lost in the middle" effect (we never put the boring middle files in context)

---

## Token Efficiency Across Iterations

The system ran with a 40,000 token budget.

| Phase | Tokens Used | % of Budget |
|---|---|---|
| Graph build + export | 0 (local, no API) | 0% |
| Navigator | ~2,500 | 6% |
| Analyzer | ~4,800 | 12% |
| Fixer | ~4,100 | 10% |
| **Total used** | **~11,400** | **28.5%** |
| **Remaining** | **~28,600** | **71.5%** |

The graph-guided approach left **71.5% of the budget unused** while still finding 7 architectural bugs and proposing 12 targeted fixes.
