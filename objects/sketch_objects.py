from pydeation.objects.abstract_objects import CustomObject
from pydeation.objects.line_objects import SVG
from pydeation.xpresso.userdata import UOptions, ULength, UAngle, UGroup
from pydeation.xpresso.xpressions import XRelation, XIdentity
from pydeation.constants import *
import c4d


class Sketch(CustomObject):
    """gives useful additional parameters to SVG objects"""

    def __init__(self, file_name, rel_x=0, rel_y=0, rel_z=0, rel_rot=0, plane="xy", **kwargs):
        self.file_name = file_name
        self.plane = plane
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.rel_z = rel_z
        self.rel_rot = rel_rot
        super().__init__(**kwargs)

    def specify_parts(self):
        self.svg = SVG(self.file_name)
        self.parts.append(self.svg)

    def specify_parameters(self):
        self.plane_parameter = UOptions(
            name="Plane", options=["xy", "zy", "xz"], default_value=self.plane)
        self.relative_x_parameter = ULength(
            name="RelativeX", default_value=self.rel_x)
        self.relative_y_parameter = ULength(
            name="RelativeY", default_value=self.rel_y)
        self.relative_z_parameter = ULength(
            name="RelativeZ", default_value=self.rel_z)
        self.relative_rotation_parameter = UAngle(
            name="RelativeRotation", default_value=self.rel_rot)
        self.parameters += [self.plane_parameter, self.relative_x_parameter,
                            self.relative_y_parameter, self.relative_z_parameter, self.relative_rotation_parameter]

    def specify_relations(self):
        plane_relation_h = XRelation(part=self.svg, whole=self, desc_ids=[ROT_H], parameters=[self.plane_parameter],
                                     formula=f"if({self.plane_parameter.name}==1;Pi/2;0)")
        plane_relation_p = XRelation(part=self.svg, whole=self, desc_ids=[ROT_P], parameters=[self.plane_parameter],
                                     formula=f"if({self.plane_parameter.name}==2;-Pi/2;0)")
        relative_x_relation = XIdentity(
            part=self.svg, whole=self, desc_ids=[POS_X], parameter=self.relative_x_parameter)
        relative_y_relation = XIdentity(
            part=self.svg, whole=self, desc_ids=[POS_Y], parameter=self.relative_y_parameter)
        relative_z_relation = XIdentity(
            part=self.svg, whole=self, desc_ids=[POS_Z], parameter=self.relative_z_parameter)
        relative_rotation_relation = XIdentity(
            part=self.svg, whole=self, desc_ids=[ROT_B], parameter=self.relative_rotation_parameter)


class David(Sketch):

    def __init__(self, **kwargs):
        super().__init__("david", **kwargs)


class GitHub(Sketch):

    def __init__(self, **kwargs):
        super().__init__("github", **kwargs)


class DNA(Sketch):

    def __init__(self, **kwargs):
        super().__init__("dna", **kwargs)


class Human(Sketch):

    def __init__(self, perspective="portrait", posture="standing", **kwargs):
        description = f"human_{perspective}_{posture}"
        super().__init__(description, **kwargs)


class Fire(Sketch):

    def __init__(self, **kwargs):
        super().__init__("fire", **kwargs)


class Footprint(Sketch):

    def __init__(self, side="right", **kwargs):
        description = f"{side}_foot"
        super().__init__(description, **kwargs)
