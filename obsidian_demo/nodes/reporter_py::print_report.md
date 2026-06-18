# print_report

**Kind**: `function`  
**File**: `reporter.py`  
**Lines**: 27–34  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 1

> Print the collection report to stdout.

## Source

```python
def print_report(shapes: list) -> None:
    """Print the collection report to stdout."""
    report = collection_report(shapes)
    print(f"Shapes: {report['count']}  (circles={report['circles']}, rects={report['rectangles']})")
    print(f"Total area     : {report['total_area']:.2f}")
    print(f"Total perimeter: {report['total_perimeter']:.2f}")
    if report["largest"]:
        print(f"Largest        : {report['largest']}")
```

## Outgoing Relationships

- [[reporter_py::collection_report|collection_report]] `Extracted:calls`

## Incoming Relationships

_None — this node has no incoming edges._
