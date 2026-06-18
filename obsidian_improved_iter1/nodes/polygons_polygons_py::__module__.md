# polygons

**Kind**: `module`  
**File**: `polygons/polygons.py`  
**Lines**: 1–69  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 0

## Source

```python
import turtle

class Polygon(object):

    def __init__(self, sides, internal_angles_sum, internal_angle):
        self.sides = sides
        self.internal_angles_sum = internal_angles_sum
        self.internal_angle = internal_angle
        

# calculate the total internal angles, and the angles within
# a regular version of the polygon
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
    # … (truncated)
```

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

_None — this node has no incoming edges._
