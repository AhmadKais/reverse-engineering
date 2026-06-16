# hot.md — Architectural Hotspots

> **Sparse graph detected** (`edge_count = 0`). The files below **failed AST parsing** —
> they are the actual investigation hotspots. The centrality table only shows parseable step-files.

## ⚠️ Primary Hotspots — Failed AST Parse (Start Here)

| Priority | File | Signal | Status |
|---|---|---|---|
| 🔴 1 | `mathsquiz/mathsquiz.py` | 0 nodes extracted — syntax errors block AST | **Investigate first** |
| 🔴 2 | `polygons/polygons.py` | 0 nodes extracted — syntax errors block AST | **Investigate first** |

## Centrality Table (Parseable Nodes Only)

Nodes ranked by betweenness centrality (higher = more central = higher risk).

| Rank | Node | Kind | Betweenness | In | Out |
|------|------|------|-------------|-----|-----|
| 1 | [[mathsquiz_mathsquiz-step1_py::__module__\|mathsquiz-step1]] | module | 0.0000 | 0 | 0 |
| 2 | [[mathsquiz_mathsquiz-step3_py::__module__\|mathsquiz-step3]] | module | 0.0000 | 0 | 0 |
| 3 | [[mathsquiz_mathsquiz-step3_py::welcome_message\|welcome_message]] | function | 0.0000 | 0 | 0 |
| 4 | [[mathsquiz_mathsquiz-step3_py::ask_question\|ask_question]] | function | 0.0000 | 0 | 0 |
| 5 | [[mathsquiz_mathsquiz-step3_py::print_final_scores\|print_final_scores]] | function | 0.0000 | 0 | 0 |
| 6 | [[mathsquiz_mathsquiz-step2_py::__module__\|mathsquiz-step2]] | module | 0.0000 | 0 | 0 |
| 7 | [[mathsquiz_mathsquiz-step2_py::welcome_message\|welcome_message]] | function | 0.0000 | 0 | 0 |
| 8 | [[mathsquiz_mathsquiz-step2_py::ask_question\|ask_question]] | function | 0.0000 | 0 | 0 |
| 9 | [[mathsquiz_mathsquiz-step2_py::print_final_scores\|print_final_scores]] | function | 0.0000 | 0 | 0 |

> All betweenness = 0.0 because 0 edges exist.
> A healthy codebase of this size would show 5–50 edges.
> Universal zero = broken codebase, not a quiet one.
