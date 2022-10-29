import pydeation
import importlib
importlib.reload(pydeation.objects.abstract_objects)
from pydeation.objects.abstract_objects import LineObject
from pydeation.objects.helper_objects import Null
from pydeation.constants import *
from pydeation.xpresso.xpressions import XIdentity
import c4d
import os


class Circle(LineObject):

    def __init__(self, radius=200, ellipse_ratio=1, ring_ratio=1, **kwargs):
        self.radius = radius
        self.ellipse_ratio = ellipse_ratio
        self.ring_ratio = ring_ratio
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osplinecircle)

    def set_object_properties(self):
        # check input values
        if not 0 <= self.ring_ratio <= 1:
            raise ValueError("ring_ratio must be between 0 and 1")
        if not 0 <= self.ellipse_ratio <= 1:
            raise ValueError("ring_ratio must be between 0 and 1")
        # implicit properties
        if self.ring_ratio != 1:
            self.obj[c4d.PRIM_CIRCLE_RING] = True
        inner_radius = self.radius * self.ring_ratio
        if self.ellipse_ratio != 1:
            self.obj[c4d.PRIM_CIRCLE_ELLIPSE] = True
        ellipse_radius = self.radius * self.ellipse_ratio
        # set properties
        self.obj[c4d.PRIM_CIRCLE_RADIUSY] = ellipse_radius
        self.obj[c4d.PRIM_CIRCLE_INNER] = inner_radius
        self.obj[c4d.PRIM_CIRCLE_RADIUS] = self.radius
        # set constants
        self.obj[c4d.SPLINEOBJECT_SUB] = 32

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "radius": c4d.DescID(c4d.DescLevel(c4d.PRIM_CIRCLE_RADIUS, c4d.DTYPE_REAL, 0))
        }


class Rectangle(LineObject):

    def __init__(self, width=100, height=100, rounding=False, **kwargs):
        self.width = width
        self.height = height
        self.rounding = rounding
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osplinerectangle)

    def set_object_properties(self):
        # check input values
        if not 0 <= self.rounding <= 1:
            raise ValueError("rounding must be between 0 and 1")
        self.obj[c4d.PRIM_RECTANGLE_WIDTH] = self.width
        self.obj[c4d.PRIM_RECTANGLE_HEIGHT] = self.height
        if self.rounding:
            self.obj[c4d.PRIM_RECTANGLE_ROUNDING] = True
            rounding_radius = self.rounding * min(self.width, self.height) / 2
            self.obj[c4d.PRIM_RECTANGLE_RADIUS] = rounding_radius

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "width": c4d.DescID(c4d.DescLevel(c4d.PRIM_RECTANGLE_WIDTH, c4d.DTYPE_REAL, 0)),
            "height": c4d.DescID(c4d.DescLevel(c4d.PRIM_RECTANGLE_HEIGHT, c4d.DTYPE_REAL, 0)),
            "rounding_radius": c4d.DescID(c4d.DescLevel(c4d.PRIM_RECTANGLE_RADIUS, c4d.DTYPE_REAL, 0))
        }


class Arc(LineObject):

    def __init__(self, radius=150, start_angle=0, end_angle=PI / 2, **kwargs):
        self.radius = radius
        self.start_angle = start_angle
        self.end_angle = end_angle
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osplinearc)

    def set_object_properties(self):
        self.obj[c4d.PRIM_ARC_RADIUS] = self.radius
        self.obj[c4d.PRIM_ARC_START] = self.start_angle
        self.obj[c4d.PRIM_ARC_END] = self.end_angle

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "radius": c4d.DescID(c4d.DescLevel(c4d.PRIM_ARC_RADIUS, c4d.DTYPE_REAL, 0)),
            "start_angle": c4d.DescID(c4d.DescLevel(c4d.PRIM_ARC_START, c4d.DTYPE_REAL, 0)),
            "end_angle": c4d.DescID(c4d.DescLevel(c4d.PRIM_ARC_END, c4d.DTYPE_REAL, 0))
        }


class Spline(LineObject):
    """creates a basic spline"""

    def __init__(self, points=[], spline_type="bezier", **kwargs):
        self.points = points
        self.spline_type = spline_type
        super().__init__(**kwargs)
        self.add_points_to_spline()

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Ospline)

    def add_points_to_spline(self):
        if self.points:
            c4d_points = [c4d.Vector(*point) for point in self.points]
            point_count = len(self.points)
            self.obj.ResizeObject(point_count)
            self.obj.SetAllPoints(c4d_points)

    def set_object_properties(self):
        spline_types = {
            "linear": 0,
            "cubic": 1,
            "akima": 2,
            "b-spline": 3,
            "bezier": 4
        }
        # set interpolation
        self.obj[c4d.SPLINEOBJECT_TYPE] = spline_types[self.spline_type]


class SVG(Spline):  # takes care of importing svgs

    def __init__(self, file_name, x=0, y=0, z=0, **kwargs):
        self.file_name = file_name
        self.x = x
        self.y = y
        self.z = z
        self.extract_spline_from_vector_import()
        super().__init__(**kwargs)
        self.fix_axes()

    def extract_spline_from_vector_import(self):
        file_path = os.path.join(SVG_PATH, self.file_name + ".svg")
        vector_import = c4d.BaseObject(1057899)
        self.document = c4d.documents.GetActiveDocument()
        self.document.InsertObject(vector_import)
        vector_import[c4d.ART_FILE] = file_path
        self.document.ExecutePasses(
            bt=None, animation=False, expressions=False, caches=True, flags=c4d.BUILDFLAGS_NONE)
        vector_import.Remove()
        cache = vector_import.GetCache()
        cache = cache.GetDown()
        cache = cache.GetDown()
        cache = cache.GetDownLast()
        self.spline = cache.GetClone()

    def fix_axes(self):
        self.document.SetSelection(self.obj)  # select svg
        c4d.CallCommand(1011982)  # moves svg axes to center
        self.obj[c4d.ID_BASEOBJECT_REL_POSITION] = c4d.Vector(
            0, 0, 0)  # move svg to origin
        # set specified position
        self.set_position(x=self.x, y=self.y, z=self.z)

    def specify_object(self):
        self.obj = self.spline


class EdgeSpline(LineObject):

    def __init__(self, solid_object, mode="outline", **kwargs):
        self.solid_object = solid_object
        self.mode = mode
        super().__init__(**kwargs)
        self.insert_solid_object()
        self.fix_visibility_behaviour()

    def specify_object(self):
        self.obj = c4d.BaseObject(1057180)

    def insert_solid_object(self):
        self.solid_object.obj.InsertUnder(self.obj)

    def set_object_properties(self):
        # set mode
        modes = {
            "standard": 0,
            "curvature": 1,
            "contour": 2,
            "outline": 3,
            "intersection": 4,
        }
        self.obj[c4d.ID_MT_EDGETOSPLINE_MODE_CYCLE] = modes[self.mode]
        self.obj[c4d.ID_MT_EDGETOSPLINE_PHONG_ANGLE] = PI/9
        # join spline segments within 5cm threshold
        self.obj[c4d.ID_MT_EDGETOSPLINE_EDGESPLINE_JOIN] = True
        self.obj[c4d.ID_MT_EDGETOSPLINE_EDGESPLINE_JOIN_THRESHOLD] = 5

    def fix_visibility_behaviour(self):
        """we link the visibility of the object to the sketch tag spline type fix the visibility behaviour"""
        visibility_relation = XIdentity(
            part=self.sketch_tag, whole=self, desc_ids=[self.sketch_tag.desc_ids["render_splines"]], parameter=self.visibility_parameter, name="VisibilityInheritance")


class PySpline(LineObject):
    """turns a c4d spline into a pydeation spline"""

    def __init__(self, input_spline, spline_type="bezier", **kwargs):
        self.input_spline = self.get_spline(input_spline)
        self.spline_type = spline_type
        super().__init__(**kwargs)

    def get_spline(self, input_spline):
        # turns any primitive spline into a single editable spline
        if type(input_spline) is not c4d.SplineObject:
            pass
        return input_spline

    def specify_object(self):
        self.obj = self.input_spline.GetClone()

    def set_object_properties(self):
        spline_types = {
            "linear": 0,
            "cubic": 1,
            "akima": 2,
            "b-spline": 3,
            "bezier": 4
        }
        # set interpolation
        self.obj[c4d.SPLINEOBJECT_TYPE] = spline_types[self.spline_type]


class SplineText(LineObject):
    """creates the native text object of c4d as opposed to the customized version which has additional structure"""

    def __init__(self, text, height=50, anchor="middle", seperate_letters=False, **kwargs):
        self.text = text
        self.height = height
        self.anchor = anchor
        self.seperate_letters = seperate_letters
        super().__init__(name=text, **kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osplinetext)

    def set_object_properties(self):
        anchors = {"left": 0, "middle": 1, "right": 0}
        self.obj[c4d.PRIM_TEXT_TEXT] = self.text
        self.obj[c4d.PRIM_TEXT_HEIGHT] = self.height
        self.obj[c4d.PRIM_TEXT_ALIGN] = anchors[self.anchor]
        self.obj[c4d.PRIM_TEXT_SEPARATE] = self.seperate_letters

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "text": c4d.DescID(c4d.DescLevel(c4d.PRIM_TEXT_TEXT, c4d.DTYPE_STRING, 0)),
            "text_height": c4d.DescID(c4d.DescLevel(c4d.PRIM_TEXT_HEIGHT, c4d.DTYPE_REAL, 0))
        }