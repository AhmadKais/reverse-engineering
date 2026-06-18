# Rectangle

**Kind**: `class`  
**File**: `shapes.py`  
**Lines**: 30–44  
**Betweenness Centrality**: 0.0000  
**In-degree**: 1 | **Out-degree**: 1

> Axis-aligned rectangle defined by width and height.

## Source

```python
class Rectangle(Shape):
    """Axis-aligned rectangle defined by width and height."""

    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

    def is_square(self) -> bool:
        return self.width == self.height
```

## Inherits From

- [[Shape]]

## Methods

- `__init__`
- `area`
- `perimeter`
- `is_square`

## Outgoing Relationships

- [[shapes_py::Shape|Shape]] `Extracted:inherits`

## Incoming Relationships

- [[calculator_py::__module__|calculator]] `Extracted:imports`
