"""FIXED: polygons/polygons.py — all bugs corrected by the Fixer agent.

Bugs fixed:
  1. class Polygon(Object) → class Polygon(object)   [SyntaxError: undefined name Object]
  2. new Polygon(...)      → Polygon(...)             [SyntaxError: 'new' not Python syntax]
  3. Hardcoded internal_angles_sum/internal_angle →  formula: (sides-2)*180 / sides
  4. draw_polygon hardcoded to hexagon (range 6, angle 60) → uses polygon_details
"""

import turtle


class Polygon(object):       # FIX 1: lowercase 'object'

    def __init__(self, sides, internal_angles_sum, internal_angle):
        self.sides = sides
        self.internal_angles_sum = internal_angles_sum
        self.internal_angle = internal_angle


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


sides = int(input("How many sides does your polygon have?: "))
polygon_details = calc_polygon_details(sides)

print("    Sides:", polygon_details["sides"])
print("    Internal angles sum:", polygon_details["internal_angles_sum"])
print("    Internal angles:", polygon_details["internal_angles"])

draw = input("Would you like me to draw it? (Y/n): ")
if draw == "" or draw.lower() == "y":
    draw_polygon(polygon_details)
