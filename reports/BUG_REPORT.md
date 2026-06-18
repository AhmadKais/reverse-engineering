# Bug Report — martinpeck/broken-python

Target repository: `data/broken-python/`  
Source: https://github.com/martinpeck/broken-python  
Analysis mode: **sparse-graph fallback** (graph had 9 nodes, 0 edges — syntax errors prevented AST parsing)

---

## Why the graph was sparse

The main source files (`mathsquiz.py`, `polygons.py`) contain Python 2 syntax and undefined keywords that make them **unparseable by Python 3's AST module**:

```
SyntaxError: Missing parentheses in call to 'print'   ← Python 2 print
SyntaxError: invalid syntax  ← 'new Polygon(...)' — 'new' is not Python
SyntaxError: invalid syntax  ← 'if answer = 55' — assignment in condition
SyntaxError: invalid syntax  ← 'else if' — should be 'elif'
```

This triggered the **sparse-graph conditional branch** in the LangGraph workflow:  
`build_graph → raw_reader → analyze → fix`  
instead of the normal `build_graph → navigate → analyze → fix`.

---

## File: `polygons/polygons.py`

### Bug 1 — `class Polygon(Object)` → undefined name [CRITICAL]

**Type**: NameError / OOP Bug  
**Evidence**: `class Polygon(Object):` — `Object` (capital O) does not exist in Python; this is syntactically valid but raises `NameError: name 'Object' is not defined` at runtime  
**Root cause**: JavaScript/Java habit carried into Python (`Object` is the Java base class)  
**Fix**: `class Polygon(object):` (lowercase, or simply `class Polygon:` in Python 3)

### Bug 2 — `new Polygon(...)` → invalid syntax [CRITICAL]

**Type**: SyntaxError  
**Evidence**: `poly = new Polygon(sides, internal_angles_sum, internal_angles)`  
**Root cause**: `new` keyword does not exist in Python (it's Java/JavaScript)  
**Fix**: `poly = Polygon(sides, internal_angles_sum, internal_angles)`

### Bug 3 — Hardcoded wrong polygon formulas [MAJOR]

**Type**: Logic Bug  
**Evidence**:
```python
if sides == 3:
    internal_angles_sum = 180    # correct
elif sides == 4:
    internal_angles_sum = 360    # correct
else:
    internal_angles_sum = 1000   # WRONG — hardcoded nonsense
    internal_angles = 200        # WRONG
```
**Root cause**: Incomplete implementation with a magic number fallback  
**Fix**: Use the standard formula:
```python
internal_angles_sum = (sides - 2) * 180
internal_angle = internal_angles_sum / sides
```

### Bug 4 — `draw_polygon` always draws a hexagon [MAJOR]

**Type**: Logic Bug  
**Evidence**:
```python
for i in range(0, 6):      # always 6 sides
    t.forward(length_of_edge)
    t.right(60)             # always 60° — only correct for hexagon
```
**Root cause**: TODO comment in the code acknowledges this; never implemented  
**Fix**:
```python
sides = polygon_details["sides"]
for i in range(sides):
    t.forward(length_of_edge)
    t.right(360 / sides)    # exterior angle formula
```

---

## File: `mathsquiz/mathsquiz.py`

### Bug 5 — Python 2 print statements [CRITICAL]

**Type**: SyntaxError  
**Evidence**: `print "Hello! ..."` — Python 2 syntax  
**Fix**: `print("Hello! ...")`

### Bug 6 — Assignment `=` used instead of equality `==` in conditions [CRITICAL]

**Type**: SyntaxError  
**Evidence**: `if answer = 55:` — all 6 questions use `=`  
**Fix**: `if int(answer) == 56:` (also cast to int, since `input()` returns str)

### Bug 7 — Wrong answers for every question [MAJOR]

**Type**: Logic Bug

| Question | Code says | Correct |
|---|---|---|
| 8 × 7 | 55 | **56** |
| 4 × 9 | 49 | **36** |
| 12 × 6 | 126 | **72** |
| 6 × 8 | 668 | **48** |
| 7 × 7 | 77 | **49** |
| 11 × 6 | 60 | **66** |

### Bug 8 — Score never incremented [MAJOR]

**Type**: Logic Bug  
**Evidence**: `score = 0` is set but `score += 1` is never called anywhere  
**Root cause**: The increment was forgotten; the final score will always print 0

### Bug 9 — Only 6 questions instead of 10 [MAJOR]

**Type**: Logic Bug  
**Evidence**: Code says "I'm going to ask you 10 maths questions" but only 6 exist  
**Fix**: Add questions 7–10

### Bug 10 — All questions labelled "Question 1:" [MINOR]

**Type**: Logic Bug  
**Evidence**: Every `print("Question 1:")` — copy-paste error  
**Fix**: Correct numbering 1–10

### Bug 11 — `else if` instead of `elif` [CRITICAL]

**Type**: SyntaxError  
**Evidence**: `else if score < 8:` — not valid Python  
**Fix**: `elif score < 8:`

### Bug 12 — `if score = 10` in final block [CRITICAL]

**Type**: SyntaxError  
**Evidence**: `else if score = 10:` — assignment in condition  
**Fix**: `elif score == 10:`

---

## Summary Table

| # | File | Bug | Type | Severity | Status |
|---|---|---|---|---|---|
| 1 | polygons.py | `class Polygon(Object)` | OOP SyntaxError | Critical | ✅ Fixed |
| 2 | polygons.py | `new Polygon(...)` | SyntaxError | Critical | ✅ Fixed |
| 3 | polygons.py | Wrong angle formula | Logic Bug | Major | ✅ Fixed |
| 4 | polygons.py | draw always hexagon | Logic Bug | Major | ✅ Fixed |
| 5 | mathsquiz.py | Python 2 print | SyntaxError | Critical | ✅ Fixed |
| 6 | mathsquiz.py | `=` not `==` in if | SyntaxError | Critical | ✅ Fixed |
| 7 | mathsquiz.py | Wrong answers | Logic Bug | Major | ✅ Fixed |
| 8 | mathsquiz.py | Score never incremented | Logic Bug | Major | ✅ Fixed |
| 9 | mathsquiz.py | Only 6 questions | Logic Bug | Major | ✅ Fixed |
| 10 | mathsquiz.py | All labelled "Question 1:" | Logic Bug | Minor | ✅ Fixed |
| 11 | mathsquiz.py | `else if` not `elif` | SyntaxError | Critical | ✅ Fixed |
| 12 | mathsquiz.py | `if score = 10` | SyntaxError | Critical | ✅ Fixed |

**All 12 bugs fixed.** Corrected files: `artifacts/fixed_polygons.py`, `artifacts/fixed_mathsquiz.py`  
Both files parse cleanly under Python 3.12 (`ast.parse()` verified).
