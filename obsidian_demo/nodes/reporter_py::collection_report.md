# collection_report

**Kind**: `function`  
**File**: `reporter.py`  
**Lines**: 12–24  
**Betweenness Centrality**: 0.0178  
**In-degree**: 1 | **Out-degree**: 6

> Build a full statistical report for a collection of shapes.

## Source

```python
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
```

## Outgoing Relationships

- [[calculator_py::filter_circles|filter_circles]] `Extracted:calls`
- [[calculator_py::filter_rectangles|filter_rectangles]] `Extracted:calls`
- [[calculator_py::largest_shape|largest_shape]] `Extracted:calls`
- [[calculator_py::total_area|total_area]] `Extracted:calls`
- [[calculator_py::total_perimeter|total_perimeter]] `Extracted:calls`
- [[reporter_py::shape_summary|shape_summary]] `Extracted:calls`

## Incoming Relationships

- [[reporter_py::print_report|print_report]] `Extracted:calls`
