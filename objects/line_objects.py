from pydeation.objects.abstract_objects import LineObject
from pydeation.objects.helper_objects import Null, Group
from pydeation.constants import *
import c4d

class Circle(LineObject):

    def __init__(self, radius=200, ellipse_ratio=1, ring_ratio=1, **kwargs):
        super().__init__(**kwargs)
        self.set_object_properties(
            radius=radius, ellipse_ratio=ellipse_ratio, ring_ratio=ring_ratio)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osplinecircle)

    def set_object_properties(self, radius=200, ellipse_ratio=1, ring_ratio=1):
        # check input values
        if not 0 <= ring_ratio <= 1:
            raise ValueError("ring_ratio must be between 0 and 1")
        if not 0 <= ellipse_ratio <= 1:
            raise ValueError("ring_ratio must be between 0 and 1")
        # implicit properties
        if ring_ratio != 1:
            self.obj[c4d.PRIM_CIRCLE_RING] = True
        inner_radius = radius * ring_ratio
        if ellipse_ratio != 1:
            self.obj[c4d.PRIM_CIRCLE_ELLIPSE] = True
        ellipse_radius = radius * ellipse_ratio
        # set properties
        self.obj[c4d.PRIM_CIRCLE_RADIUSY] = ellipse_radius
        self.obj[c4d.PRIM_CIRCLE_INNER] = inner_radius
        self.obj[c4d.PRIM_CIRCLE_RADIUS] = radius
        # set constants
        self.obj[c4d.SPLINEOBJECT_SUB] = 32


class Tracer(LineObject):

    def __init__(self, *nodes, spline_type="bezier", tracing_mode="path", reverse=False, **kwargs):
        super().__init__(**kwargs)
        self.set_object_properties(
            *nodes, spline_type=spline_type, tracing_mode=tracing_mode, reverse=reverse)

    def specify_object(self):
        self.obj = c4d.BaseObject(1018655)

    def set_object_properties(self, *nodes, spline_type="bezier", tracing_mode="path", reverse=False):
        # implicit properties
        trace_list = c4d.InExcludeData()
        for node in nodes:
            trace_list.InsertObject(node.obj, 1)
            node.obj.InsertUnder(self.obj)
        # set properties
        self.obj[c4d.MGTRACEROBJECT_OBJECTLIST] = trace_list
        spline_types = {"bezier": 4, "linear": 0}
        self.obj[c4d.SPLINEOBJECT_TYPE] = spline_types[spline_type]
        self.obj[c4d.MGTRACEROBJECT_REVERSESPLINE] = reverse
        tracing_modes = {"path": 0, "objects": 1, "elements": 2}
        # tracing mode to object
        self.obj[c4d.MGTRACEROBJECT_MODE] = tracing_modes[tracing_mode]
        # set constants
        self.obj[c4d.SPLINEOBJECT_INTERPOLATION] = 1  # adaptive
        self.obj[c4d.MGTRACEROBJECT_USEPOINTS] = False  # no vertex tracing
        self.obj[c4d.MGTRACEROBJECT_SPACE] = False  # global space

class Arrow(Tracer):

    def __init__(self, start_point, stop_point, arrow_start=False, arrow_end=True, **kwargs):
        self.create_nulls(start_point, stop_point)
        super().__init__(self.start_null, self.stop_null, arrow_start=arrow_start,
                         arrow_end=arrow_end, spline_type="linear", tracing_mode="objects", **kwargs)
        self.make_nulls_children()

    def create_nulls(self, start_point, stop_point):
        self.start_null = Null(
            name="StartPoint", x=start_point[0], y=start_point[1], z=start_point[2])
        self.stop_null = Null(
            name="StopPoint", x=stop_point[0], y=stop_point[1], z=stop_point[2])

    def make_nulls_children(self):
        self.start_null.obj.InsertUnder(self.obj)
        self.stop_null.obj.InsertUnder(self.obj)


class Spline(LineObject):
    """turns a c4d spline into a pydeation spline"""

    def __init__(self, input_spline, spline_type="bezier", **kwargs):
        self.input_spline = input_spline
        super().__init__(**kwargs)
        self.set_object_properties(spline_type=spline_type)

    def specify_object(self):
        self.obj = self.input_spline.GetClone()

    def set_object_properties(self, spline_type="bezier"):
        spline_types = {
            "linear": 0,
            "cubic": 1,
            "akima": 2,
            "b-spline": 3,
            "bezier": 4
        }
        # set interpolation
        self.obj[c4d.SPLINEOBJECT_TYPE] = spline_types[spline_type]


class Text(LineObject):

    def __init__(self, text, height=50, anchor="middle", **kwargs):
        super().__init__(**kwargs)
        self.set_object_properties(text, height=height, anchor=anchor)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osplinetext)

    def set_object_properties(self, text, height=50, anchor="middle"):
        # write properties to self
        self.text = text
        # implicit properties
        anchors = {"left": 0, "middle": 1, "right": 0}
        # set properties
        self.obj[c4d.PRIM_TEXT_TEXT] = text
        self.obj[c4d.PRIM_TEXT_HEIGHT] = height
        # set constants
        self.obj[c4d.PRIM_TEXT_ALIGN] = anchors[anchor]
        self.obj[c4d.PRIM_TEXT_SEPARATE] = True


class Letters(Text):
    """converts a text object into a group of separate letters"""

    def __init__(self, text, height=50, anchor="middle", **kwargs):
        super().__init__(text=text, height=height, anchor=anchor, **kwargs)
        self.seperate_letters(kwargs)

    def seperate_letters(self, kwargs):
        text_editable = c4d.utils.SendModelingCommand(command=c4d.MCOMMAND_MAKEEDITABLE, list=[
            self.obj], mode=c4d.MODELINGCOMMANDMODE_ALL, doc=self.document)
        # unpack letters
        letters = self.unpack(text_editable[0])
        pydeation_letters = []
        # convert to pydeation letters
        for letter in letters:
            # get coordinates
            # matrix
            matrix = letter.GetMg()
            # position
            x, y, z = matrix.off.x, matrix.off.y, matrix.off.z
            # rotation
            h, p, b = c4d.utils.MatrixToHPB(matrix).x, c4d.utils.MatrixToHPB(
                matrix).y, c4d.utils.MatrixToHPB(matrix).z
            # scale
            scale_x, scale_y, scale_z = matrix.GetScale(
            ).x, matrix.GetScale().y, matrix.GetScale().z
            # create pydeation letter
            if "x" not in kwargs:
                kwargs["x"] = 0
            if "y" not in kwargs:
                kwargs["y"] = 0
            if "z" not in kwargs:
                kwargs["z"] = 0
            pydeation_letter = Spline(letter, x=x - kwargs["x"], y=y, z=z - kwargs["z"], h=h, p=p, b=b, scale_x=scale_x, scale_y=scale_y,
                                      scale_z=scale_z)
            pydeation_letters.append(pydeation_letter)
        # create text from letters
        self = Group(*pydeation_letters, name=self.text, **kwargs)

    @staticmethod
    def unpack(parent):
        """unpacks the children from the hierarchy"""
        children = []
        for child in parent.GetChildren():
            children.append(child)
        return children

    def has_lines(self):
        """check if new lines present"""
        if "\n" in self.text:
            return True
        else:
            return False
