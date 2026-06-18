# calc_polygon_details

**Kind**: `function`  
**File**: `polygons/polygons.py`  
**Lines**: 13–36  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 1

## Source

```python
def calc_polygon_details(sides):

    internal_angles_sum = 0
    internal_angles = 0

    # TODO: find a better way to work this stuff out
    if sides == 3:
        internal_angles_sum = 180
        internal_angles = 60
    elif sides == 4:
        internal_angles_sum = 360
        internal_angles = 90
    else:
        internal_angles_sum = 1000
        internal_angles = 200

    poly = Polygon(sides, internal_angles_sum, internal_angles)
    print(poly)

    # return a dictionary containing info about the polygon
    # TODO: perhaps I should use the class Polygon instead!
    return {"sides": sides,
            "internal_angles_sum": internal_angles_sum,
            "internal_angles": internal_angles}
```

## Outgoing Relationships

- [[polygons_polygons_py::Polygon|Polygon]] `Extracted:calls`

## Incoming Relationships

_None — this node has no incoming edges._
