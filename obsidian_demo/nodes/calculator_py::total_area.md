# total_area

**Kind**: `function`  
**File**: `calculator.py`  
**Lines**: 6–8  
**Betweenness Centrality**: 0.0030  
**In-degree**: 2 | **Out-degree**: 1

> Sum the area of every shape in the list.

## Source

```python
def total_area(shapes: list) -> float:
    """Sum the area of every shape in the list."""
    return sum(s.area() for s in shapes)
```

## Outgoing Relationships

- [[shapes_py::Shape_area|Shape.area]] `Extracted:calls`

## Incoming Relationships

- [[reporter_py::collection_report|collection_report]] `Extracted:calls`
- [[reporter_py::__module__|reporter]] `Extracted:imports`
