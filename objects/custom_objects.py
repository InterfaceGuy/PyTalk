from abc import abstractmethod
from pydeation.objects.abstract_objects import CustomObject
from pydeation.objects.line_objects import Line, Arc, Circle, Rectangle, Text, Tracer, Spline
from pydeation.objects.sketch_objects import Human, Fire, Footprint
from pydeation.objects.helper_objects import *
from pydeation.xpresso.userdata import UAngle, UGroup, ULength, UOptions, UCompletion, UText
from pydeation.xpresso.xpressions import XRelation, XIdentity, XClosestPointOnSpline, XScaleBetweenPoints
from pydeation.animation.abstract_animators import AnimationGroup
from pydeation.animation.sketch_animators import Draw, UnDraw
from pydeation.tags import XPressoTag
from pydeation.constants import *
import c4d


class Eye(CustomObject):

    def specify_parts(self):
        self.upper_lid = Line((0, 0, 0), (200, 0, 0), name="UpperLid")
        self.lower_lid = Line((0, 0, 0), (200, 0, 0), name="LowerLid")
        self.eyeball = Arc(name="Eyeball")
        self.parts += [self.upper_lid, self.lower_lid, self.eyeball]

    def specify_parameters(self):
        self.opening_angle = UAngle(name="OpeningAngle")
        self.parameters += [self.opening_angle]

    def specify_relations(self):
        upper_lid_relation = XRelation(part=self.upper_lid, whole=self, desc_ids=[ROT_B],
                                       parameters=[self.opening_angle], formula="-OpeningAngle/2")
        lower_lid_relation = XRelation(part=self.lower_lid, whole=self, desc_ids=[ROT_B],
                                       parameters=[self.opening_angle], formula="OpeningAngle/2")
        eyeball_start_angle_relation = XRelation(
            part=self.eyeball, whole=self, desc_ids=[self.eyeball.desc_ids["start_angle"]], parameters=[self.opening_angle], formula="-OpeningAngle/2")
        eyeball_end_angle_relation = XRelation(
            part=self.eyeball, whole=self, desc_ids=[self.eyeball.desc_ids["end_angle"]], parameters=[self.opening_angle], formula="OpeningAngle/2")


class PhysicalCampfire(CustomObject):

    def specify_parts(self):
        self.circle = Circle(plane="xz")
        self.left_human = Human(
            x=-50, perspective="portrait", posture="standing")
        self.right_human = Human(
            x=50, perspective="portrait", posture="standing")
        self.humans = Group(self.left_human, self.right_human)
        self.fire = Fire()
        self.symbol = Rectangle()
        self.parts += [self.circle, self.humans, self.fire, self.symbol]


class ProjectLiminality(CustomObject):

    def specify_parts(self):
        self.big_circle = Circle(radius=100, color=BLUE)
        self.small_circle = Circle(radius=50, y=50, color=RED)
        self.left_line = Line((-70, -50, 0), (0, 50, 0))
        self.right_line = Line((70, -50, 0), (0, 50, 0))
        self.lines = Group(self.left_line, self.right_line, name="Lines")
        self.parts += [self.big_circle, self.small_circle, self.lines]


class Node(CustomObject):
    """creates a node object with an optional label and symbol"""

    def __init__(self, text=None, text_position="center", text_height=20, symbol=None, rounding=1 / 4, width=100, height=50, **kwargs):
        self.rounding = rounding
        self.width = width
        self.height = height
        self.text = text
        self.text_height = text_height
        self.symbol = symbol
        if self.symbol:
            self.text_position = "bottom"
        else:
            self.text_position = text_position
        super().__init__(**kwargs)

    def specify_parts(self):
        self.border = Rectangle(name="Border", rounding=1)
        self.parts.append(self.border)
        if self.text:
            self.label = Text(self.text)
            self.parts.append(self.label)
        if self.symbol:
            self.parts.append(self.symbol)

    def specify_parameters(self):
        self.width_parameter = ULength(name="Width", default_value=self.width)
        self.height_parameter = ULength(
            name="Height", default_value=self.height)
        self.rounding_parameter = UCompletion(
            name="Rounding", default_value=self.rounding)
        self.parameters = [self.width_parameter, self.height_parameter,
                           self.rounding_parameter]
        if self.symbol:
            self.symbol_border_parameter = UCompletion(
                name="SymbolBorder", default_value=1 / 4)
            self.parameters.append(self.symbol_border_parameter)
        if self.text:
            self.text_parameter = UText(name="Label", default_value=self.text)
            self.text_position_parameter = UOptions(name="TextPosition", options=[
                "center", "top", "bottom"], default_value=self.text_position)
            self.text_height_parameter = ULength(
                name="TextSize", default_value=self.text_height)
            self.parameters += [self.text_parameter,
                                self.text_position_parameter, self.text_height_parameter]

    def specify_relations(self):
        width_relation = XIdentity(
            part=self.border, whole=self, desc_ids=[self.border.desc_ids["width"]], parameter=self.width_parameter)
        height_relation = XIdentity(
            part=self.border, whole=self, desc_ids=[self.border.desc_ids["height"]], parameter=self.height_parameter)
        rounding_relation = XRelation(part=self.border, whole=self, desc_ids=[self.border.desc_ids[
                                      "rounding_radius"]], parameters=[self.rounding_parameter, self.width_parameter, self.height_parameter], formula=f"min({self.width_parameter.name};{self.height_parameter.name})/2*Rounding")
        if self.text:
            text_relation = XIdentity(
                part=self.label, whole=self, desc_ids=[self.label.desc_ids["text"]], parameter=self.text_parameter)
            text_position_relation = XRelation(part=self.label, whole=self, desc_ids=[POS_Y], parameters=[
                self.text_position_parameter, self.height_parameter, self.text_height_parameter], formula=f"if({self.text_position_parameter.name}==0;-{self.text_height_parameter.name}/2;if({self.text_position_parameter.name}==1;{self.height_parameter.name}/2+5;-{self.height_parameter.name}/2-5-{self.text_height_parameter.name}))")
            text_size_relation = XIdentity(
                part=self.label, whole=self, desc_ids=[self.label.desc_ids["text_height"]], parameter=self.text_height_parameter)
        if self.symbol:
            symbol_scale_relation = XRelation(part=self.symbol, whole=self, desc_ids=[self.symbol.diameter_parameter.desc_id], parameters=[self.width_parameter, self.height_parameter, self.symbol_border_parameter],
                                              formula=f"(1-{self.symbol_border_parameter.name})*min({self.width_parameter.name};{self.height_parameter.name})")


class MonoLogosNode(Node):

    def __init__(self, text="MonoLogos", symbol=None, width=75, height=75, rounding=1, **kwargs):
        self.symbol = symbol if symbol else ProjectLiminality()
        super().__init__(text=text, width=width, height=height,
                         rounding=rounding, symbol=self.symbol, **kwargs)


class DiaLogosNode(Node):

    def __init__(self, text="DiaLogos", **kwargs):
        super().__init__(text=text, **kwargs)


class Connection(CustomObject):
    """creates a connection line between two given objects"""

    def __init__(self, start_object, target_object, turbulence=False, turbulence_vector=(0, 40, 0), turbulence_frequency=8, **kwargs):
        self.start_object = start_object
        self.start_object_is_node = issubclass(
            self.start_object.__class__, Node)
        self.target_object = target_object
        self.target_object_is_node = issubclass(
            self.target_object.__class__, Node)
        self.turbulence = turbulence
        self.turbulence_vector = turbulence_vector
        self.turbulence_frequency = turbulence_frequency
        super().__init__(**kwargs)

    def specify_parts(self):
        trace_start = self.start_object
        trace_target = self.target_object
        if self.start_object_is_node:
            self.spline_point_start = Null(name="SplinePointStart")
            self.parts.append(self.spline_point_start)
            trace_start = self.spline_point_start
        if self.target_object_is_node:
            self.spline_point_target = Null(name="SplinePointTarget")
            self.parts.append(self.spline_point_target)
            trace_target = self.spline_point_target
        self.linear_path = Tracer(trace_start, trace_target,
                                  tracing_mode="objects", name="LinearPath", visible=False)
        self.parts.append(self.linear_path)
        if self.turbulence:
            # remove linear path sketch material
            self.linear_path.sketch_material.obj.Remove()
            self.spherical_field = SphericalField()
            self.random_effector = RandomEffector(
                position=self.turbulence_vector, fields=[self.spherical_field])
            self.turbulent_path = Spline(name="TurbulentPath")
            self.mospline = MoSpline(source_spline=self.linear_path, point_count=self.turbulence_frequency, destination_spline=self.turbulent_path, effectors=[
                                     self.random_effector])
            self.parts += [self.spherical_field, self.turbulent_path,
                           self.random_effector, self.mospline]

    def specify_relations(self):
        point_a = self.start_object
        point_b = self.target_object
        if self.start_object_is_node:
            start_point_on_spline_relation = XClosestPointOnSpline(
                spline_point=self.spline_point_start, reference_point=self.target_object, target=self, spline=self.start_object.border)
            point_a = self.spline_point_start
        if self.target_object_is_node:
            target_point_on_spline_relation = XClosestPointOnSpline(
                spline_point=self.spline_point_target, reference_point=self.start_object, target=self, spline=self.target_object.border)
            point_b = self.spline_point_target
        if self.turbulence:
            field_between_points_relation = XScaleBetweenPoints(
                scaled_object=self.spherical_field, point_a=point_a, point_b=point_b, target=self)


class FootPath(CustomObject):

    def __init__(self, path=None, left_foot=None, right_foot=None, foot_size=10, step_length=10, step_width=20, scale_zone_length=10, floor_plane="xy", path_completion=1, **kwargs):
        self.path = path
        self.left_foot = left_foot if left_foot else Footprint(
            side="left")
        self.right_foot = right_foot if right_foot else Footprint(
            side="right")
        self.foot_size = foot_size
        self.step_length = step_length
        self.step_width = step_width
        self.scale_zone_length = scale_zone_length
        self.floor_plane = floor_plane
        self.path_completion = path_completion
        super().__init__(**kwargs)

    def specify_parts(self):
        self.linear_field = LinearField(length=10)
        self.plain_effector = PlainEffector(
            fields=[self.linear_field], scale=-1)
        self.cloner = Cloner(target_object=self.path, clones=[self.left_foot, self.right_foot],
                             effectors=[self.plain_effector], step_size=self.step_length)
        self.parts += [self.linear_field, self.plain_effector, self.cloner]

    def specify_parameters(self):
        self.offset_start_parameter = UCompletion(name="OffsetStart")
        self.offset_end_parameter = UCompletion(name="OffsetEnd")
        self.foot_size_parameter = ULength(
            name="FootSize", default_value=self.foot_size)
        self.step_length_parameter = ULength(
            name="StepLength", default_value=self.step_length)
        self.step_width_parameter = ULength(
            name="StepWidth", default_value=self.step_width)
        self.floor_plane_parameter = UOptions(
            name="FloorPlane", options=["xy", "zy", "xz"], default_value=self.floor_plane)
        self.scale_zone_length_parameter = ULength(
            name="ScaleZoneLength", default_value=self.scale_zone_length)
        self.path_completion_parameter = UCompletion(
            name="PathCompletion", default_value=self.path_completion)
        self.parameters += [self.offset_start_parameter, self.offset_end_parameter, self.step_length_parameter,
                            self.step_width_parameter, self.floor_plane_parameter, self.scale_zone_length_parameter,
                            self.path_completion_parameter, self.foot_size_parameter]

    #def specify_relations(self):
     #   step_width_left_foot_relation = XRelation(part=self.left_foot)
