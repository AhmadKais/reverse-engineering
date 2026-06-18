# calculator

**Kind**: `module`  
**File**: `calculator.py`  
**Lines**: 1–28  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 3

> Calculator module — computes aggregate statistics over collections of shapes.

## Source

```python
"""Calculator module — computes aggregate statistics over collections of shapes."""

from shapes import Circle, Rectangle, Shape


def total_area(shapes: list) -> float:
    """Sum the area of every shape in the list."""
    return sum(s.area() for s in shapes)


def total_perimeter(shapes: list) -> float:
    """Sum the perimeter of every shape in the list."""
    return sum(s.perimeter() for s in shapes)


def largest_shape(shapes: list) -> Shape:
    """Return the shape with the greatest area."""
    return max(shapes, key=lambda s: s.area())


def filter_circles(shapes: list) -> list:
    """Return only Circle instances from the list."""
    return [s for s in shapes if isinstance(s, Circle)]


def filter_rectangles(shapes: list) -> list:
    """Return only Rectangle instances from the list."""
    return [s for s in shapes if isinstance(s, Rectangle)]
```

## Outgoing Relationships

- [[shapes_py::Circle|Circle]] `Extracted:imports`
- [[shapes_py::Rectangle|Rectangle]] `Extracted:imports`
- [[shapes_py::Shape|Shape]] `Extracted:imports`

## Incoming Relationships

_None — this node has no incoming edges._
