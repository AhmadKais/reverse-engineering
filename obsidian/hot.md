# hot.md — Investigation Hotspots

This page is the **focused entry point for bug investigation**. It identifies which files are the real hotspots and why — before and after graph analysis.

---

## ⚠️ Primary Hotspots — Failed AST Parse (Critical Signal)

The graph builder attempted to parse all 5 files. Two files **failed completely** — they produced 0 nodes and 0 edges. This is the strongest possible signal of broken code.

| Priority | File | Why It's a Hotspot | Status |
|---|---|---|---|
| 🔴 1 | `polygons/polygons.py` | AST parse **failed** — 0 nodes extracted | Broken (Python 2 OOP + `new` keyword) |
| 🔴 2 | `mathsquiz/mathsquiz.py` | AST parse **failed** — 0 nodes extracted | Broken (Python 2 `print`, `=` in conditions) |

**How to investigate**:
- See [[investigation]] for the full investigation trace
- See [[BEFORE_AFTER]] for before/after at graph + code level
- See `reports/BUG_REPORT.md` for all 12 bugs

---

## 📊 Graph Centrality — Parseable Nodes

These nodes were extracted from the 3 parseable step-files. All have **betweenness = 0.0** because the broken files prevent any call/import edges from forming.

| Rank | Node | Kind | Betweenness | In | Out |
|------|------|------|-------------|-----|-----|
| 1 | [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step1_py::__module__\|mathsquiz-step1]] | module | 0.0000 | 0 | 0 |
| 2 | [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step3_py::__module__\|mathsquiz-step3]] | module | 0.0000 | 0 | 0 |
| 3 | [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step3_py::welcome_message\|welcome_message]] | function | 0.0000 | 0 | 0 |
| 4 | [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step3_py::ask_question\|ask_question]] | function | 0.0000 | 0 | 0 |
| 5 | [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step3_py::print_final_scores\|print_final_scores]] | function | 0.0000 | 0 | 0 |
| 6 | [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step2_py::__module__\|mathsquiz-step2]] | module | 0.0000 | 0 | 0 |
| 7 | [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step2_py::welcome_message\|welcome_message]] | function | 0.0000 | 0 | 0 |
| 8 | [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step2_py::ask_question\|ask_question]] | function | 0.0000 | 0 | 0 |
| 9 | [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step2_py::print_final_scores\|print_final_scores]] | function | 0.0000 | 0 | 0 |

> **Key insight**: All betweenness = 0.0 across 9 nodes is not normal for a real project. A healthy 2-file Python project would show at least 5–10 call/import edges. Universal zero = broken codebase.

---

## 🔍 What the 0-Edge Graph Tells Us

```
Graph summary: 9 nodes, 0 edges
is_sparse = True  (threshold: < 5 edges)
→ LangGraph routes to: raw_reader (not navigate)
→ Files sent to LLM: polygons.py + mathsquiz.py ONLY
→ Step files excluded from LLM context (0 tokens wasted on them)
```

The sparse-graph signal is **free intelligence** — it cost 0 tokens to determine which 2 files are broken and which 3 are fine.

---

## 🐛 Bugs Found (Summary)

| File | Bugs | Types |
|---|---|---|
| `polygons/polygons.py` | 5 | 3× SyntaxError, 2× Logic |
| `mathsquiz/mathsquiz.py` | 11 | 4× SyntaxError, 7× Logic |
| **Total** | **16** | |

Full details: [[investigation]] · `reports/BUG_REPORT.md`
