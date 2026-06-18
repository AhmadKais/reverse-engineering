# Circle

**Kind**: `class`  
**File**: `shapes.py`  
**Lines**: 17–27  
**Betweenness Centrality**: 0.0000  
**In-degree**: 1 | **Out-degree**: 1

> Circle defined by radius.

## Source

```python
class Circle(Shape):
    """Circle defined by radius."""

    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return 3.14159 * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * 3.14159 * self.radius
```

## Inherits From

- [[Shape]]

## Methods

- `__init__`
- `area`
- `perimeter`

## Outgoing Relationships

- [[shapes_py::Shape|Shape]] `Extracted:inherits`

## Incoming Relationships

- [[calculator_py::__module__|calculator]] `Extracted:imports`
