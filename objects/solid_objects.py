from pydeation.objects.abstract_objects import SolidObject
import c4d


class Sphere(SolidObject):

    def __init__(self, radius=100, **kwargs):
        super().__init__(**kwargs)
        self.set_object_properties(radius=radius)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Osphere)

    def set_object_properties(self, radius=100):
        # set properties
        self.obj[c4d.PRIM_SPHERE_RAD] = radius
        self.obj[c4d.PRIM_SPHERE_TYPE] = 4  # set type to icosahedron


class Cylinder(SolidObject):

    def __init__(self, radius=50, **kwargs):
        super().__init__(**kwargs)
        self.set_object_properties(radius=radius)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Ocylinder)

    def set_object_properties(self, radius=50, height=200):
        # set properties
        self.obj[c4d.PRIM_CYLINDER_RADIUS] = radius
        self.obj[c4d.PRIM_CYLINDER_HEIGHT] = height
