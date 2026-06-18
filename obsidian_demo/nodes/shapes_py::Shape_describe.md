# Shape.describe

**Kind**: `method`  
**File**: `shapes.py`  
**Lines**: 13–14  
**Betweenness Centrality**: 0.0040  
**In-degree**: 1 | **Out-degree**: 2

## Source

```python
    def describe(self) -> str:
        return f"{self.__class__.__name__}: area={self.area():.2f}, perimeter={self.perimeter():.2f}"
```

## Outgoing Relationships

- [[shapes_py::Shape_area|Shape.area]] `Extracted:calls`
- [[shapes_py::Shape_perimeter|Shape.perimeter]] `Extracted:calls`

## Incoming Relationships

- [[reporter_py::shape_summary|shape_summary]] `Extracted:calls`
