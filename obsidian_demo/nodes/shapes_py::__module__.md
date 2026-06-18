# shapes

**Kind**: `module`  
**File**: `shapes.py`  
**Lines**: 1–44  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 0

> Geometry module — base class and two concrete shapes.

## Source

```python
"""Geometry module — base class and two concrete shapes."""


class Shape:
    """Abstract base for all geometric shapes."""

    def area(self) -> float:
        raise NotImplementedError

    def perimeter(self) -> float:
        raise NotImplementedError

    def describe(self) -> str:
        return f"{self.__class__.__name__}: area={self.area():.2f}, perimeter={self.perimeter():.2f}"


class Circle(Shape):
    """Circle defined by radius."""

    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return 3.14159 * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * 3.14159 * self.radius


class Rectangle(Shape):
    # … (truncated)
```

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

_None — this node has no incoming edges._
