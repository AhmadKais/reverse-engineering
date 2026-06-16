# Polygon

**Kind**: `class`  
**File**: `fixed_polygons.py`  
**Lines**: 13–18  
**Betweenness Centrality**: 0.0000  
**In-degree**: 1 | **Out-degree**: 0

## Source

```python
class Polygon(object):       # FIX 1: lowercase 'object'

    def __init__(self, sides, internal_angles_sum, internal_angle):
        self.sides = sides
        self.internal_angles_sum = internal_angles_sum
        self.internal_angle = internal_angle
```

## Inherits From

- [[object]]

## Methods

- `__init__`

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

- [[fixed_polygons_py::calc_polygon_details|calc_polygon_details]] `Extracted:calls`
