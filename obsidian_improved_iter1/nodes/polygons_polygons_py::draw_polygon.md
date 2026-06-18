# draw_polygon

**Kind**: `function`  
**File**: `polygons/polygons.py`  
**Lines**: 41–53  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 0

## Source

```python
def draw_polygon(polygon_details):

    # set up the screen and turtle
    scr = turtle.Screen()
    t = turtle.Turtle()
    t.pen(pencolor="red", pensize=2, fillcolor="green")

    length_of_edge = 50
    
    # TODO: make this work for any type of polygon
    for i in range(0, 6):
        t.forward(length_of_edge)
        t.right(60)
```

## Outgoing Relationships

_None — this node has no outgoing edges._

## Incoming Relationships

_None — this node has no incoming edges._
