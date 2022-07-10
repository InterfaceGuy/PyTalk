from abc import abstractmethod
from pydeation.objects.abstract_objects import HelperObject
from c4d.modules.mograph import FieldLayer
import numpy as np
import c4d


class Null(HelperObject):

    def __init__(self, display="dot", **kwargs):
        super().__init__(**kwargs)
        self.set_object_properties(display=display)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Onull)

    def set_object_properties(self, display="dot"):
        # implicit properties
        shapes = {"dot": 0, "cross": 1, "circle": 2, None: 14}
        # set properties
        self.obj[c4d.NULLOBJECT_DISPLAY] = shapes[display]


class Group(Null):

    def __init__(self, *children, **kwargs):
        super().__init__(**kwargs)
        self.children = list(children)
        self.add_children()

    def __iter__(self):
        self.idx = 0
        return self

    def __next__(self):
        if self.idx < len(self.children):
            child = self.children[self.idx]
            self.idx += 1
            return child
        else:
            raise StopIteration

    def __getitem__(self, index):
        return self.children[index]

    def add_children(self):
        for child in self.children[::-1]:
            child.obj.InsertUnder(self.obj)

    def add(self, *children):
        for child in children:
            self.children.append(child)
            child.obj.InsertUnder(self.obj)

    def position_on_spline(self, spline):
        """positions the children the given spline"""
        number_of_children = len(self.children)
        editable_spline = spline.get_editable()
        for i, child in enumerate(self.children):
            child_position = editable_spline.GetSplinePoint(
                i / number_of_children)
            child.set_position(position=child_position)

    def position_on_circle(self, radius=100, x=0, y=0, z=0, plane="xy", at_bottom=None, at_top=None):
        """positions the children on a circle"""
        def position(radius, phi, plane):
            if plane == "xy":
                return c4d.Vector(radius * np.sin(phi), radius * np.cos(phi), 0)
            if plane == "zy":
                return c4d.Vector(0, radius * np.cos(phi), radius * np.sin(phi))
            if plane == "xz":
                return c4d.Vector(radius * np.sin(phi), 0, radius * np.cos(phi))

        number_of_children = len(self.children)
        phi_offset = 0  # angle offset if necessary
        if at_bottom:
            phi_offset = np.pi
        phis = [
            phi + phi_offset for phi in np.linspace(0, 2 * np.pi, number_of_children + 1)]

        child_positions = [position(radius, phi, plane) for phi in phis]

        children = self.children
        index = None
        if at_top:
            index = self.children.index(at_top)
        elif at_bottom:
            index = self.children.index(at_bottom)
        if index:
            # reorder children using index
            children = self.children[index:] + self.children[:index]
        for child, child_position in zip(children, child_positions):
            child.set_position(position=child_position)

    def position_on_line(self, point_ini=(-100, 0, 0), point_fin=(100, 0, 0)):
        """positions the children on a line"""
        number_of_children = len(self.children)
        vector_ini = c4d.Vector(*point_ini)
        vector_fin = c4d.Vector(*point_fin)
        child_positions = [t * (vector_fin - vector_ini) +
                           vector_ini for t in np.linspace(0, 1, number_of_children)]
        for child, child_position in zip(self.children, child_positions):
            child.set_position(position=child_position)


class MoSpline(HelperObject):

    def __init__(self, mode="spline", generation_mode="even", point_count=100, source_spline=None, effectors=[], **kwargs):
        super().__init__(**kwargs)
        self.set_object_properties(
            mode=mode, generation_mode=generation_mode, point_count=point_count, source_spline=source_spline, effectors=effectors)

    def specify_object(self):
        self.obj = c4d.BaseObject(440000054)

    def set_object_properties(self, mode="spline", generation_mode="even", point_count=100, source_spline=None, effectors=[]):
        # implicit properties
        modes = {"simple": 0, "spline": 1, "turtle": 2}
        generation_modes = {"vertex": 0, "count": 1, "even": 2, "step": 3}
        # set properties
        self.obj[c4d.MGMOSPLINEOBJECT_MODE] = modes[mode]
        self.obj[c4d.MGMOSPLINEOBJECT_SPLINE_MODE] = generation_modes[generation_mode]
        self.obj[c4d.MGMOSPLINEOBJECT_SPLINE_COUNT] = point_count
        if source_spline:
            self.obj[c4d.MGMOSPLINEOBJECT_SOURCE_SPLINE] = source_spline.obj
        self.add_effectors(*effectors)

    def add_effectors(self, *effectors):
        effector_list = c4d.InExcludeData()
        for effector in effectors:
            effector_list.InsertObject(effector.obj, 1)
        self.obj[c4d.MGMOSPLINEOBJECT_EFFECTORLIST] = effector_list


class SplineEffector(HelperObject):

    def __init__(self, spline=None, segment_mode="index", segment_index=0, transform_mode="absolute", fields=[], **kwargs):
        super().__init__(**kwargs)
        self.set_object_properties(spline=spline, segment_mode=segment_mode,
                                   segment_index=segment_index, transform_mode=transform_mode, fields=fields)

    def specify_object(self):
        self.obj = c4d.BaseObject(1018774)

    def set_object_properties(self, spline=None, segment_mode="index", segment_index=0, transform_mode="absolute", fields=[]):
        # yin properties
        segment_modes = {"index": 0, "even_spacing": 1,
                         "random": 2, "full_spacing": 3}
        transform_modes = {"relative_to_node": 0,
                           "absolute": 1, "relative_to_spline": 2}
        field_list = c4d.FieldList()
        for field in fields:
            field_layer = FieldLayer(c4d.FLfield)
            field_layer.SetLinkedObject(field.obj)
            field_list.InsertLayer(field_layer)
        # yang properties
        if spline:
            self.obj[c4d.MGSPLINEEFFECTOR_SPLINE] = spline.obj
        self.obj[c4d.MGSPLINEEFFECTOR_SEGMENTMODE] = segment_modes[segment_mode]
        self.obj[c4d.MGSPLINEEFFECTOR_SEGMENTINDEX] = segment_index
        self.obj[c4d.MGSPLINEEFFECTOR_TRANSFORMMODE] = transform_modes[transform_mode]
        self.obj[c4d.FIELDS] = field_list


class LinearField(HelperObject):

    def __init__(self, length=100, direction="x+", **kwargs):
        super().__init__(**kwargs)
        self.set_object_properties(length=length, direction=direction)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Flinear)

    def set_object_properties(self, length=100, direction="x+"):
        # yin properties
        directions = {"x+": 0, "x-": 1, "y+": 2, "y-": 3, "z+": 4, "z-": 5}
        contour_modes = {None: 0, "quadratic": 1,
                         "step": 2, "quantize": 3, "curve": 4}
        self.obj[c4d.FIELD_CONTOUR_MODE] = contour_modes["curve"]
        # yang properties
        self.obj[c4d.LINEAR_SIZE] = length
        self.obj[c4d.LINEAR_DIRECTION] = directions[direction]


class SphericalField(HelperObject):

    def __init__(self, radius=100, **kwargs):
        super().__init__(**kwargs)
        self.set_object_properties(radius=radius)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Fspherical)

    def set_object_properties(self, radius=100):
        # yin properties
        self.obj[c4d.FIELD_INNER_OFFSET] = 1  # results in constant function
        # yang properties
        self.obj[c4d.LINEAR_SIZE] = radius
