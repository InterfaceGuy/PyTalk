import c4d
import numpy as np

# helper functions


def _average_color(color1, color2):
    # gives the correct average of two colors
    x1 = color1.x
    y1 = color1.y
    z1 = color1.z

    x2 = color2.x
    y2 = color2.y
    z2 = color2.z

    average_x = (x1**2 + x2**2) / 2**0.5
    average_y = (y1**2 + y2**2) / 2**0.5
    average_z = (z1**2 + z2**2) / 2**0.5

    average_color = c4d.Vector(average_x, average_y, average_z)

    return average_color


# colors
BLUE = c4d.Vector(0, 153, 204) / 255
RED = c4d.Vector(255, 126, 121) / 255
PURPLE = _average_color(RED, BLUE)
YELLOW = c4d.Vector(218, 218, 88) / 255
GREEN = c4d.Vector(71, 196, 143) / 255
WHITE = c4d.Vector(255, 255, 255) / 255
BLACK = c4d.Vector(0, 0, 0) / 255

# material constants
FILLER_TRANSPARENCY = 0.93
VG_THICKNESS = 5
TEXT_THICKNESS = 5
PRIM_THICKNESS = 5
SPLINE_THICKNESS = 3

# math
PI = np.pi

# paths
SVG_PATH = "/Users/davidrug/Library/Preferences/Maxon/Maxon Cinema 4D R25_EBA43BEE/python39/libs/pydeationlib/assets/svg"