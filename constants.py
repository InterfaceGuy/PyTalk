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

# missing descIds xpresso ports
REAL_DESCID_IN = c4d.DescID(c4d.DescLevel(1000019, 400007003, 1001144))
REAL_DESCID_OUT = c4d.DescID(c4d.DescLevel(536870931, 400007003, 1001144))
BOOL_DESCID_IN = c4d.DescID(c4d.DescLevel(401006001, 400007001, 1001144))
BOOL_DESCID_OUT = c4d.DescID(c4d.DescLevel(936876913, 400007001, 1001144))
INTEGER_DESCID_IN = c4d.DescID(c4d.DescLevel(1000015, 400007002, 1001144))
INTEGER_DESCID_OUT = c4d.DescID(c4d.DescLevel(536870927, 400007002, 1001144))
COLOR_DESCID_IN = c4d.DescID(c4d.DescLevel(1000003, 400007004, 1001144))
COLOR_DESCID_OUT = c4d.DescID(c4d.DescLevel(536870915, 400007004, 1001144))
VALUE_DESCID_IN = c4d.DescID(c4d.DescLevel(2000, 400007003, 400001133))
CONDITION_DESCID_IN = c4d.DescID(c4d.DescLevel(2000, 400007003, 400001117))
CONDITION_SWITCH_DESCID_IN = c4d.DescID(c4d.DescLevel(4005, 400007003, 1022471))