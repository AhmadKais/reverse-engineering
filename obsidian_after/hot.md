# hot.md — Architectural Hotspots (AFTER FIX)

> This is the **post-fix state** of the vault. The graph was rebuilt on `artifacts/fixed_polygons.py` and `artifacts/fixed_mathsquiz.py` after all bugs were corrected.  
> Compare with the pre-fix vault in `obsidian/` where both files had 0 nodes.

---

## What Changed

| Metric | Before (buggy) | After (fixed) |
|---|---|---|
| Nodes | 9 (step-files only) | 6 (fixed files now parseable) |
| Edges | 0 | 1 (Polygon instantiation edge) |
| Polygon class visible | ❌ (parse error) | ✅ |
| calc_polygon_details visible | ❌ | ✅ |
| draw_polygon visible | ❌ | ✅ |

The `Polygon` class, `calc_polygon_details`, and `draw_polygon` are now visible to the graph — they were completely hidden before because `class Polygon(Object)` and `new Polygon(...)` caused SyntaxErrors.

---

## Nodes Ranked by Betweenness Centrality

| Rank | Node | Kind | Betweenness | In | Out |
|------|------|------|-------------|-----|-----|
| 1 | [[artifacts_fixed_polygons_py::__module__\|fixed_polygons]] | module | 0.0000 | 0 | 0 |
| 2 | [[artifacts_fixed_polygons_py::Polygon\|Polygon]] | class | 0.0000 | 1 | 0 |
| 3 | [[artifacts_fixed_polygons_py::Polygon___init__\|Polygon.__init__]] | method | 0.0000 | 0 | 0 |
| 4 | [[artifacts_fixed_polygons_py::calc_polygon_details\|calc_polygon_details]] | function | 0.0000 | 0 | 1 |
| 5 | [[artifacts_fixed_polygons_py::draw_polygon\|draw_polygon]] | function | 0.0000 | 0 | 0 |
| 6 | [[artifacts_fixed_mathsquiz_py::__module__\|fixed_mathsquiz]] | module | 0.0000 | 0 | 0 |

> **Note**: Betweenness remains 0 because `fixed_mathsquiz.py` is still a flat script with no function definitions. `Polygon` has In=1 (calc_polygon_details instantiates it) and `calc_polygon_details` has Out=1.
