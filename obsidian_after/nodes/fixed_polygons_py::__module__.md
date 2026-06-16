# fixed_polygons

**Kind**: `module`  
**File**: `fixed_polygons.py`  
**Lines**: 1–61  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 0

> FIXED: polygons/polygons.py — all bugs corrected by the Fixer agent.

Bugs fixed:
  1. class Polygon(Object) → class Polygon(object)   [SyntaxError: undefined name Object]
  2. new Polygon(...)      →

## Source

```python
"""FIXED: polygons/polygons.py — all bugs corrected by the Fixer agent.

Bugs fixed:
  1. class Polygon(Object) → class Polygon(object)   [SyntaxError: undefined name Object]
  2. new Polygon(...)      → Polygon(...)             [SyntaxError: 'new' not Python syntax]
  3. Hardcoded internal_angles_sum/internal_angle →  formula: (sides-2)*180 / sides
  4. draw_polygon hardcoded to hexagon (range 6, angle 60) → uses polygon_details
"""

import turtle


class Polygon(object):       # FIX 1: lowercase 'object'

    def __init__(self, sides, internal_angles_sum, internal_angle):
        self.sides = sides
        self.internal_angles_sum = internal_angles_sum
        self.internal_angle = internal_angle


def calc_polygon_details(sides):
    # FIX 3: use the correct formula instead of hardcoded values
    internal_angles_sum = (sides - 2) * 180
    internal_angle = internal_angles_sum / sides

    poly = Polygon(sides, internal_angles_sum, internal_angle)  # FIX 2: no 'new' keyword
    print(poly)

    return {
        "sides": sides,
    # … (truncated)
```

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

_None — this node has no incoming edges._
