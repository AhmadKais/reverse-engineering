# Shape

**Kind**: `class`  
**File**: `shapes.py`  
**Lines**: 4–14  
**Betweenness Centrality**: 0.0000  
**In-degree**: 4 | **Out-degree**: 0

> Abstract base for all geometric shapes.

## Source

```python
class Shape:
    """Abstract base for all geometric shapes."""

    def area(self) -> float:
        raise NotImplementedError

    def perimeter(self) -> float:
        raise NotImplementedError

    def describe(self) -> str:
        return f"{self.__class__.__name__}: area={self.area():.2f}, perimeter={self.perimeter():.2f}"
```

## Methods

- `area`
- `perimeter`
- `describe`

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

- [[shapes_py::Circle|Circle]] `Extracted:inherits`
- [[shapes_py::Rectangle|Rectangle]] `Extracted:inherits`
- [[reporter_py::__module__|reporter]] `Extracted:imports`
- [[calculator_py::__module__|calculator]] `Extracted:imports`
