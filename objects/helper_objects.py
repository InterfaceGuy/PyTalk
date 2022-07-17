from abc import abstractmethod
from pydeation.objects.abstract_objects import ProtoObject
from c4d.modules.mograph import FieldLayer
import numpy as np
import c4d


class Null(ProtoObject):

    def __init__(self, display="dot", **kwargs):
        self.display = display
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Onull)

    def set_object_properties(self):
        # implicit properties
        shapes = {"dot": 0, "cross": 1, "circle": 2, None: 14}
        # set properties
        self.obj[c4d.NULLOBJECT_DISPLAY] = shapes[self.display]


class Group(Null):

    def __init__(self, *children, **kwargs):
        self.children = list(children)
        super().__init__(**kwargs)
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


class Cloner(ProtoObject):

    def __init__(self, mode="object", clones=[], effectors=[], target_object=None, step_size=10, **kwargs):
        self.mode = mode
        self.clones = clones
        self.effectors = effectors
        self.target_object = target_object
        self.step_size = step_size
        super().__init__(**kwargs)
        self.insert_clones()
        self.add_effectors()

    def specify_object(self):
        self.obj = c4d.BaseObject(1018544)

    def set_object_properties(self):
        modes = {
            "object": 0,
            "linear": 1,
            "radial": 2,
            "grid": 3,
            "honeycomb": 4
        }
        self.obj[c4d.ID_MG_MOTIONGENERATOR_MODE] = modes[self.mode]
        if self.mode == "object":
            self.obj[c4d.MG_OBJECT_LINK] = self.target_object.obj
            self.obj[c4d.MG_SPLINE_MODE] = 1
            self.obj[c4d.MG_SPLINE_STEP] = self.step_size

    def insert_clones(self):
        for clone in self.clones:
            clone.obj.InsertUnder(self.obj)

    def add_effectors(self):
        effector_list = c4d.InExcludeData()
        for effector in self.effectors:
            effector_list.InsertObject(effector.obj, 1)
        self.obj[c4d.ID_MG_MOTIONGENERATOR_EFFECTORLIST] = effector_list


class MoSpline(ProtoObject):

    def __init__(self, mode="spline", generation_mode="even", point_count=100, source_spline=None, destination_spline=None, effectors=[], **kwargs):
        self.mode = mode
        self.generation_mode = generation_mode
        self.point_count = point_count
        self.source_spline = source_spline
        self.effectors = effectors
        self.destination_spline = destination_spline
        super().__init__(**kwargs)
        self.add_effectors()

    def specify_object(self):
        self.obj = c4d.BaseObject(440000054)

    def set_object_properties(self):
        # implicit properties
        modes = {"simple": 0, "spline": 1, "turtle": 2}
        generation_modes = {"vertex": 0, "count": 1, "even": 2, "step": 3}
        # set properties
        self.obj[c4d.MGMOSPLINEOBJECT_MODE] = modes[self.mode]
        self.obj[c4d.MGMOSPLINEOBJECT_SPLINE_MODE] = generation_modes[self.generation_mode]
        self.obj[c4d.MGMOSPLINEOBJECT_SPLINE_COUNT] = self.point_count
        if self.source_spline:
            self.obj[c4d.MGMOSPLINEOBJECT_SOURCE_SPLINE] = self.source_spline.obj
        if self.destination_spline:
            self.obj[c4d.MGMOSPLINEOBJECT_DEST_SPLINE] = self.destination_spline.obj

    def add_effectors(self):
        effector_list = c4d.InExcludeData()
        for effector in self.effectors:
            effector_list.InsertObject(effector.obj, 1)
        self.obj[c4d.MGMOSPLINEOBJECT_EFFECTORLIST] = effector_list


class Effector(ProtoObject):

    def __init__(self, fields=[], position=None, rotation=None, scale=None, **kwargs):
        self.fields = fields
        self.position = position
        self.rotation = rotation
        self.scale = scale
        super().__init__(**kwargs)
        self.insert_fields()
        self.set_transformation_data()

    def insert_fields(self):
        field_list = c4d.FieldList()
        for field in self.fields:
            field_layer = FieldLayer(c4d.FLfield)
            field_layer.SetLinkedObject(field.obj)
            field_list.InsertLayer(field_layer)
        self.obj[c4d.FIELDS] = field_list

    def set_transformation_data(self):
        # ensure position is off by default
        self.obj[c4d.ID_MG_BASEEFFECTOR_POSITION_ACTIVE] = False
        if self.position:
            self.obj[c4d.ID_MG_BASEEFFECTOR_POSITION_ACTIVE] = True
            self.obj[c4d.ID_MG_BASEEFFECTOR_POSITION] = c4d.Vector(
                *self.position)
        if self.rotation:
            self.obj[c4d.ID_MG_BASEEFFECTOR_ROTATION_ACTIVE] = True
            self.obj[c4d.ID_MG_BASEEFFECTOR_ROTATION] = c4d.Vector(
                *self.rotation)
        if type(self.scale) in (float, int, tuple, list):
            self.obj[c4d.ID_MG_BASEEFFECTOR_SCALE_ACTIVE] = True
            if type(self.scale) in (float, int):
                self.obj[c4d.ID_MG_BASEEFFECTOR_UNIFORMSCALE] = True
                self.obj[c4d.ID_MG_BASEEFFECTOR_USCALE] = self.scale
            else:
                self.obj[c4d.ID_MG_BASEEFFECTOR_SCALE] = c4d.Vector(
                    *self.scale)


class SplineEffector(Effector):

    def __init__(self, spline=None, segment_mode="index", segment_index=0, transform_mode="absolute", **kwargs):
        self.spline = spline
        self.segment_mode = segment_mode
        self.segment_index = segment_index
        self.transform_mode = transform_mode
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(1018774)

    def set_object_properties(self):
        # yin properties
        segment_modes = {"index": 0, "even_spacing": 1,
                         "random": 2, "full_spacing": 3}
        transform_modes = {"relative_to_node": 0,
                           "absolute": 1, "relative_to_spline": 2}
        # yang properties
        if self.spline:
            self.obj[c4d.MGSPLINEEFFECTOR_SPLINE] = self.spline.obj
        self.obj[c4d.MGSPLINEEFFECTOR_SEGMENTMODE] = segment_modes[self.segment_mode]
        self.obj[c4d.MGSPLINEEFFECTOR_SEGMENTINDEX] = self.segment_index
        self.obj[c4d.MGSPLINEEFFECTOR_TRANSFORMMODE] = transform_modes[self.transform_mode]


class RandomEffector(Effector):

    def __init__(self, mode="random", **kwargs):
        self.mode = mode
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(1018643)

    def set_object_properties(self):
        random_modes = {
            "random": 0,
            "gaussian": 1,
            "noise": 2,
            "turbulence": 3,
            "sorted": 4
        }
        self.obj[c4d.MGSPLINEEFFECTOR_TRANSFORMMODE] = random_modes[self.mode]


class PlainEffector(Effector):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(1021337)

    def set_object_properties(self):
        pass


class LinearField(ProtoObject):

    def __init__(self, length=100, direction="x+", **kwargs):
        self.length = length
        self.direction = direction
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Flinear)

    def set_object_properties(self):
        # yin properties
        directions = {"x+": 0, "x-": 1, "y+": 2, "y-": 3, "z+": 4, "z-": 5}
        contour_modes = {None: 0, "quadratic": 1,
                         "step": 2, "quantize": 3, "curve": 4}
        self.obj[c4d.FIELD_CONTOUR_MODE] = contour_modes["curve"]
        # yang properties
        self.obj[c4d.LINEAR_SIZE] = self.length
        self.obj[c4d.LINEAR_DIRECTION] = directions[self.direction]


class SphericalField(ProtoObject):

    def __init__(self, radius=100, **kwargs):
        self.radius = radius
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Fspherical)

    def set_object_properties(self):
        # yin properties
        self.obj[c4d.FIELD_INNER_OFFSET] = 1  # results in constant function
        # yang properties
        self.obj[c4d.LINEAR_SIZE] = self.radius
