# calc_polygon_details

**Kind**: `function`  
**File**: `fixed_polygons.py`  
**Lines**: 21–33  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 1

## Source

```python
def calc_polygon_details(sides):
    # FIX 3: use the correct formula instead of hardcoded values
    internal_angles_sum = (sides - 2) * 180
    internal_angle = internal_angles_sum / sides

    poly = Polygon(sides, internal_angles_sum, internal_angle)  # FIX 2: no 'new' keyword
    print(poly)

    return {
        "sides": sides,
        "internal_angles_sum": internal_angles_sum,
        "internal_angles": internal_angle,
    }
```

## Outgoing Relationships

- [[fixed_polygons_py::Polygon|Polygon]] `Extracted:calls`

## Incoming Relationships

_None — this node has no incoming edges._
