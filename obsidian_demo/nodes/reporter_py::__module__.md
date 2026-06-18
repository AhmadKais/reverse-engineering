# reporter

**Kind**: `module`  
**File**: `reporter.py`  
**Lines**: 1–34  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 6

> Reporter module — formats shape statistics into human-readable summaries.

## Source

```python
"""Reporter module — formats shape statistics into human-readable summaries."""

from calculator import filter_circles, filter_rectangles, largest_shape, total_area, total_perimeter
from shapes import Shape


def shape_summary(shape: Shape) -> str:
    """Return a single-line summary for one shape."""
    return shape.describe()


def collection_report(shapes: list) -> dict:
    """Build a full statistical report for a collection of shapes."""
    circles = filter_circles(shapes)
    rects = filter_rectangles(shapes)
    biggest = largest_shape(shapes) if shapes else None
    return {
        "count": len(shapes),
        "circles": len(circles),
        "rectangles": len(rects),
        "total_area": total_area(shapes),
        "total_perimeter": total_perimeter(shapes),
        "largest": shape_summary(biggest) if biggest else None,
    }


def print_report(shapes: list) -> None:
    """Print the collection report to stdout."""
    report = collection_report(shapes)
    print(f"Shapes: {report['count']}  (circles={report['circles']}, rects={report['rectangles']})")
    # … (truncated)
```

## Outgoing Relationships

- [[calculator_py::filter_circles|filter_circles]] `Extracted:imports`
- [[calculator_py::filter_rectangles|filter_rectangles]] `Extracted:imports`
- [[calculator_py::largest_shape|largest_shape]] `Extracted:imports`
- [[calculator_py::total_area|total_area]] `Extracted:imports`
- [[calculator_py::total_perimeter|total_perimeter]] `Extracted:imports`
- [[shapes_py::Shape|Shape]] `Extracted:imports`

## Incoming Relationships

_None — this node has no incoming edges._
