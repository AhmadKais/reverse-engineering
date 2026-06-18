# shape_summary

**Kind**: `function`  
**File**: `reporter.py`  
**Lines**: 7–9  
**Betweenness Centrality**: 0.0040  
**In-degree**: 1 | **Out-degree**: 1

> Return a single-line summary for one shape.

## Source

```python
def shape_summary(shape: Shape) -> str:
    """Return a single-line summary for one shape."""
    return shape.describe()
```

## Outgoing Relationships

- [[shapes_py::Shape_describe|Shape.describe]] `Extracted:calls`

## Incoming Relationships

- [[reporter_py::collection_report|collection_report]] `Extracted:calls`
