# Before / After — Investigation & Fix

This note documents what we understood **before** running the pipeline, what the agents discovered, and how our understanding of the architecture changed **after** the fix.

---

## Before Investigation

### What we could see (without running the pipeline)

Opening `obsidian/` in Obsidian showed **9 isolated nodes** with **0 edges**:

```
mathsquiz-step1  (module)
  welcome_message  (function)
  ask_question     (function)
  print_final_scores (function)

mathsquiz-step2  (module)
  welcome_message  (function)
  ...

mathsquiz-step3  (module)
  ...
```

**What was invisible**: `polygons.py` and `mathsquiz.py` produced no nodes at all — AST parsing failed silently. The `Polygon` class, `calc_polygon_details`, `draw_polygon` — none of these appeared in Obsidian.

### Initial assumption

Looking at the step files in Obsidian, the system appeared to be:
- A math quiz with 3 clean functions (`welcome_message`, `ask_question`, `print_final_scores`)
- No polygon code visible whatsoever
- Seemingly well-structured

### The real signal: `hot.md`

```
| Node                | Betweenness | In | Out |
|---------------------|-------------|----|----|
| mathsquiz-step1     | 0.0000      | 0  | 0  |
| welcome_message     | 0.0000      | 0  | 0  |
| ...all 9 nodes...   | 0.0000      | 0  | 0  |
```

All centrality = 0. **This is not a quiet codebase — it's a broken one.** A real 2-file Python project would have at least 5–10 call/import edges.

---

## What the Agents Found

The sparse graph (0 edges < threshold of 5) triggered the **`raw_reader` fallback branch**:

```
build_graph (9 nodes, 0 edges)
    └── is_sparse = True
         └── raw_reader reads polygons.py + mathsquiz.py directly
              └── AnalyzerAgent → 16 bugs
                   └── FixerAgent → 18 fix proposals
```

### Bugs discovered

**polygons.py** (5 bugs):
| # | Bug | Type |
|---|-----|------|
| 1 | `class Polygon(Object)` | SyntaxError — `Object` not defined |
| 2 | `poly = new Polygon(...)` | SyntaxError — `new` not Python |
| 3 | `internal_angles_sum = 1000` for any polygon | Logic — wrong formula |
| 4 | `draw_polygon` always loops 6 times at 60° | Logic — hardcoded hexagon |
| 5 | Truncated `return` dictionary | SyntaxError — incomplete code |

**mathsquiz.py** (11 bugs):
| # | Bug | Type |
|---|-----|------|
| 1 | `print "Hello"` | SyntaxError — Python 2 |
| 2 | `if answer = 55` | SyntaxError — assignment in condition |
| 3–8 | All 6 answers wrong (e.g. 8×7=55) | Logic |
| 9 | `score` never incremented | Logic |
| 10 | All questions print "Question 1:" | Logic |
| 11 | `else if` instead of `elif` | SyntaxError |

---

## After Investigation & Fix

### Architecture understanding — completely changed

| Aspect | Before | After |
|--------|--------|-------|
| Files visible in graph | 3/6 (step files only) | Would be 6/6 with fixed files |
| Polygon class | Invisible (parse error) | `class Polygon(object)` with `__init__` |
| Nodes | 9 | 17+ (class + methods + functions now visible) |
| Edges | 0 | 9+ (imports, calls, inheritance now traceable) |
| Architecture pattern | Unknown — God Script appearance | `Polygon` OOP + factory function + renderer |

### Before / After code

**polygons.py — class declaration:**
```python
# BEFORE
class Polygon(Object):        # NameError: Object undefined

# AFTER
class Polygon(object):        # correct Python 3 base class
```

**polygons.py — instantiation:**
```python
# BEFORE
poly = new Polygon(sides, internal_angles_sum, internal_angles)  # SyntaxError

# AFTER
poly = Polygon(sides, internal_angles_sum, internal_angles)      # correct
```

**polygons.py — formula:**
```python
# BEFORE
else:
    internal_angles_sum = 1000   # arbitrary placeholder
    internal_angles = 200

# AFTER
internal_angles_sum = (sides - 2) * 180   # correct for any polygon
internal_angle = internal_angles_sum / sides
```

**mathsquiz.py — condition + answer:**
```python
# BEFORE
if answer = 55:       # SyntaxError + wrong answer

# AFTER
if int(answer) == 56:  # comparison, type cast, correct answer
    score += 1         # score now actually incremented
```

---

## What Changed in Our Understanding

1. **The step files are the intended future state** — the `mathsquiz-step2.py` functions (`welcome_message`, `ask_question`, `print_final_scores`) show exactly how `mathsquiz.py` should be refactored.

2. **`polygons.py` is actually OOP code** — it has a class, a factory, and a renderer. The bugs hid this completely from the graph.

3. **The 0-edge graph was not a failure** — it was the most important finding. It told us immediately: *"don't trust this code at the language level."*

4. **Token efficiency**: The graph told us to skip the step files entirely. They never entered the LLM context. Only `polygons.py` and `mathsquiz.py` were sent — saving ~3,800 characters (~950 tokens) of irrelevant context.

---

## Fixed Files

- [`artifacts/fixed_polygons.py`](../artifacts/fixed_polygons.py)
- [`artifacts/fixed_mathsquiz.py`](../artifacts/fixed_mathsquiz.py)

Both parse cleanly under Python 3.12: `ast.parse()` succeeds on both.
