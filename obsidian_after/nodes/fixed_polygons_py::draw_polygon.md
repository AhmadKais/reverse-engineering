# draw_polygon

**Kind**: `function`  
**File**: `fixed_polygons.py`  
**Lines**: 36–49  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 0

## Source

```python
def draw_polygon(polygon_details):
    scr = turtle.Screen()
    t = turtle.Turtle()
    t.pen(pencolor="red", pensize=2, fillcolor="green")

    length_of_edge = 50
    sides = polygon_details["sides"]
    exterior_angle = 360 / sides   # FIX 4: derive turn angle from sides

    for i in range(sides):         # FIX 4: loop the right number of times
        t.forward(length_of_edge)
        t.right(exterior_angle)

    scr.mainloop()
```

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

_None — this node has no incoming edges._
