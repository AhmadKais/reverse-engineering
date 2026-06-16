# index.md — Knowledge Graph Index

Central navigation page for the `broken-python` reverse-engineering vault.

---

## Investigation Pages

| Page | Purpose |
|---|---|
| [[hot]] | Investigation hotspots — buggy files + centrality table |
| [[investigation]] | Step-by-step investigation trace (graph → agents → fixes) |
| [[research-questions]] | All 8 research questions answered |
| [[BEFORE_AFTER]] | Before/after at graph + code level |

---

## ⚠️ Files That Failed AST Parse (Primary Targets)

These files produced **0 nodes** in the graph — they are the actual buggy files.

| File | Reason for 0 nodes | Bugs |
|---|---|---|
| `polygons/polygons.py` | `class Polygon(Object)` + `new` keyword — syntax errors block AST | 5 bugs |
| `mathsquiz/mathsquiz.py` | Python 2 `print`, `=` in conditions — syntax errors block AST | 11 bugs |

---

## ✅ Parseable Nodes (From Step-Files)

These files parsed cleanly and appear in the graph. They contain the *intended* refactored architecture.

### Functions (6)

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step3_py::ask_question|ask_question]] — `mathsquiz-step3.py`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step2_py::ask_question|ask_question]] — `mathsquiz-step2.py`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step3_py::print_final_scores|print_final_scores]] — `mathsquiz-step3.py`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step2_py::print_final_scores|print_final_scores]] — `mathsquiz-step2.py`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step3_py::welcome_message|welcome_message]] — `mathsquiz-step3.py`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step2_py::welcome_message|welcome_message]] — `mathsquiz-step2.py`

### Modules (3)

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step1_py::__module__|mathsquiz-step1]] — `mathsquiz/mathsquiz-step1.py`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step2_py::__module__|mathsquiz-step2]] — `mathsquiz/mathsquiz-step2.py`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW4_data_broken-python_mathsquiz_mathsquiz-step3_py::__module__|mathsquiz-step3]] — `mathsquiz/mathsquiz-step3.py`

---

## Graph Statistics

| Metric | Value | Interpretation |
|---|---|---|
| Total nodes | 9 | Only step-file entities parsed |
| Total edges | 0 | Broken files prevent call/import edges |
| Communities | 9 | Every node isolated |
| Bridges | 0 | No structural bridges |
| is_sparse | True | < 5 edges → raw_reader branch |

---

## Schemas (In this vault)

- [[OOP_SCHEMA]] — Polygon class hierarchy + Mermaid diagram
- [[BLOCK_SCHEMA]] — Architectural block + data flow diagrams

## Reports (External)

- `reports/BUG_REPORT.md` — 12 documented bugs with root cause + fix
- `reports/TOKEN_COMPARISON.md` — Baseline vs graph-guided token usage
- `reports/GRAPH_REPORT.md` — Graph metrics + architectural insight
