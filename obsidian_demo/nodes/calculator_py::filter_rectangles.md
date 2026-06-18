# filter_rectangles

**Kind**: `function`  
**File**: `calculator.py`  
**Lines**: 26–28  
**Betweenness Centrality**: 0.0000  
**In-degree**: 2 | **Out-degree**: 0

> Return only Rectangle instances from the list.

## Source

```python
def filter_rectangles(shapes: list) -> list:
    """Return only Rectangle instances from the list."""
    return [s for s in shapes if isinstance(s, Rectangle)]
```

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

- [[reporter_py::collection_report|collection_report]] `Extracted:calls`
- [[reporter_py::__module__|reporter]] `Extracted:imports`
