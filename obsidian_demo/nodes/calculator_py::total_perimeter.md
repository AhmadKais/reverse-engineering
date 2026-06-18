# total_perimeter

**Kind**: `function`  
**File**: `calculator.py`  
**Lines**: 11–13  
**Betweenness Centrality**: 0.0059  
**In-degree**: 2 | **Out-degree**: 1

> Sum the perimeter of every shape in the list.

## Source

```python
def total_perimeter(shapes: list) -> float:
    """Sum the perimeter of every shape in the list."""
    return sum(s.perimeter() for s in shapes)
```

## Outgoing Relationships

- [[shapes_py::Shape_perimeter|Shape.perimeter]] `Extracted:calls`

## Incoming Relationships

- [[reporter_py::collection_report|collection_report]] `Extracted:calls`
- [[reporter_py::__module__|reporter]] `Extracted:imports`
