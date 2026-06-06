import turtle

class Polygon(Object):

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

    poly = new Polygon(sides, internal_angles_sum, internal_angles)
    print(poly)

    # return a dictionary containing info about the polygon
    # TODO: perhaps I should use the class Polygon instead!
    return {"sides": sides,
            "internal_angles_sum": internal_angles_sum,
            "internal_angles": internal_angles}



# draws a polygon using the turtle
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




sides = int(input("How many sides does your polygon have?: "))

polygon_details = calc_polygon_details(sides)

print("    Sides:", polygon_details["sides"])
print("    Internal angles sum:", polygon_details["internal_angles_sum"])
print("    Internal angles:", polygon_details["internal_angles"])

draw = input("Would you like me to draw it? (Y/n): ")

if draw == "" or draw.lower() == "y":
    draw_polygon(polygon_details)
        




    
