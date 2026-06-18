# largest_shape

**Kind**: `function`  
**File**: `calculator.py`  
**Lines**: 16–18  
**Betweenness Centrality**: 0.0030  
**In-degree**: 2 | **Out-degree**: 1

> Return the shape with the greatest area.

## Source

```python
def largest_shape(shapes: list) -> Shape:
    """Return the shape with the greatest area."""
    return max(shapes, key=lambda s: s.area())
```

## Outgoing Relationships

- [[shapes_py::Shape_area|Shape.area]] `Extracted:calls`

## Incoming Relationships

- [[reporter_py::collection_report|collection_report]] `Extracted:calls`
- [[reporter_py::__module__|reporter]] `Extracted:imports`
