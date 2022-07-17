from pydeation.objects.abstract_objects import SolidObject
import c4d


class Sphere(SolidObject):

    def __init__(self, radius=100, **kwargs):
        self.radius = radius
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osphere)

    def set_object_properties(self):
        # set properties
        self.obj[c4d.PRIM_SPHERE_RAD] = self.radius
        self.obj[c4d.PRIM_SPHERE_TYPE] = 4  # set type to icosahedron


class Cylinder(SolidObject):

    def __init__(self, radius=50, height=150, **kwargs):
        self.radius = radius
        self.height = height
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Ocylinder)

    def set_object_properties(self):
        # set properties
        self.obj[c4d.PRIM_CYLINDER_RADIUS] = self.radius
        self.obj[c4d.PRIM_CYLINDER_HEIGHT] = self.height
