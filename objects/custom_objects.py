from abc import abstractmethod
from pydeation.objects.abstract_objects import CustomObject
from pydeation.objects.line_objects import Line, Arc, Circle, Rectangle, Text, Tracer, Spline
from pydeation.objects.sketch_objects import Human, Fire, Footprint
from pydeation.objects.helper_objects import *
from pydeation.xpresso.userdata import UAngle, UGroup, ULength, UOptions, UCompletion, UText
from pydeation.xpresso.xpressions import XRelation, XIdentity, XClosestPointOnSpline, XScaleBetweenPoints, XSplineLength, XAlignToSpline
from pydeation.animation.abstract_animators import AnimationGroup
from pydeation.animation.sketch_animators import Draw, UnDraw
from pydeation.tags import XPressoTag
from pydeation.constants import *
import c4d


class Group(CustomObject):

    def __init__(self, *children, **kwargs):
        self.children = list(children)
        super().__init__(**kwargs)

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

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Onull)

    def specify_parts(self):
        self.parts = self.children

    """
    def add_children(self):
        for child in self.children[::-1]:
            child.obj.InsertUnder(self.obj)
    """

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

    def create_connections(self, completeness=1, turbulence=False, deterministic=True, random_seed=420, visible=True):
        nodes = self.children
        all_edges = []
        for i, start_node in enumerate(nodes):
            for target_node in nodes[i:]:
                edge = (start_node, target_node)
                all_edges.append(edge)
        if not deterministic:
            random.seed(random_seed)
        selected_edges = random.sample(
            all_edges, round(len(all_edges) * completeness))
        self.connections = []
        for edge in selected_edges:
            connection = Connection(
                *edge, turbulence=turbulence, turbulence_vector=(40, 0, 0), visible=visible)
            self.connections.append(connection)

        return self.connections


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

    def __init__(self, distance_humans=1 / 2, border_radius=50, **kwargs):
        self.distance_humans = distance_humans
        self.border_radius = border_radius
        super().__init__(**kwargs)

    def specify_parts(self):
        self.border = Circle(plane="xz")
        self.left_human = Human(perspective="portrait", posture="standing")
        self.right_human = Human(perspective="portrait", posture="standing")
        self.humans = Group(self.left_human, self.right_human, name="Humans")
        self.fire = Fire()
        self.symbol = ProjectLiminality(p=-PI / 2, diameter=20, z=-30)
        self.parts += [self.border, self.humans, self.fire, self.symbol]

    def specify_parameters(self):
        self.border_radius_parameter = ULength(
            name="BorderRadius", default_value=self.border_radius)
        self.distance_humans_parameter = UCompletion(
            name="DistanceHumans", default_value=self.distance_humans)
        self.parameters += [self.border_radius_parameter,
                            self.distance_humans_parameter]

    def specify_relations(self):
        self.border_radius_relation = XIdentity(part=self.border, whole=self, desc_ids=[
                                                self.border.desc_ids["radius"]], parameter=self.border_radius_parameter)
        self.distance_left_human_relation = XRelation(part=self.left_human, whole=self, desc_ids=[POS_X],
                                                      parameters=[self.distance_humans_parameter, self.border_radius_parameter], formula=f"-{self.distance_humans_parameter.name}*{self.border_radius_parameter.name}")
        self.distance_right_human_relation = XRelation(part=self.right_human, whole=self, desc_ids=[POS_X],
                                                       parameters=[self.distance_humans_parameter, self.border_radius_parameter], formula=f"{self.distance_humans_parameter.name}*{self.border_radius_parameter.name}")


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

    def __init__(self, start_object, target_object, turbulence=False, plane="xy", turbulence_vector=(0, 40, 0), turbulence_frequency=8, **kwargs):
        self.start_object = start_object
        self.start_object_has_border = hasattr(
            self.start_object, "border")
        self.target_object = target_object
        self.target_object_has_border = hasattr(
            self.target_object, "border")
        self.turbulence = turbulence
        self.turbulence_vector = turbulence_vector
        self.turbulence_frequency = turbulence_frequency
        super().__init__(**kwargs)

    def specify_parts(self):
        trace_start = self.start_object
        trace_target = self.target_object
        if self.start_object_has_border:
            self.spline_point_start = Null(name="SplinePointStart")
            self.parts.append(self.spline_point_start)
            trace_start = self.spline_point_start
        if self.target_object_has_border:
            self.spline_point_target = Null(name="SplinePointTarget")
            self.parts.append(self.spline_point_target)
            trace_target = self.spline_point_target
        self.linear_path = Tracer(trace_start, trace_target,
                                  tracing_mode="objects", name="LinearPath", visible=(not self.turbulence))
        self.parts.append(self.linear_path)
        self.path = self.linear_path  # use for easy access
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
            self.path = self.turbulent_path  # use for easy access

    def specify_relations(self):
        point_a = self.start_object
        point_b = self.target_object
        if self.start_object_has_border:
            start_point_on_spline_relation = XClosestPointOnSpline(
                spline_point=self.spline_point_start, reference_point=self.target_object, target=self, spline=self.start_object.border)
            point_a = self.spline_point_start
        if self.target_object_has_border:
            target_point_on_spline_relation = XClosestPointOnSpline(
                spline_point=self.spline_point_target, reference_point=self.start_object, target=self, spline=self.target_object.border)
            point_b = self.spline_point_target
        if self.turbulence:
            field_between_points_relation = XScaleBetweenPoints(
                scaled_object=self.spherical_field, point_a=point_a, point_b=point_b, target=self)


class FootPath(CustomObject):

    def __init__(self, path=None, left_foot=None, right_foot=None, foot_size=10, step_length=20, step_width=30, scale_zone_length=3, path_completion=1, **kwargs):
        self.path = path
        self.left_foot = left_foot if left_foot else Footprint(
            side="left", plane="xz")
        self.right_foot = right_foot if right_foot else Footprint(
            side="right", plane="xz")
        self.foot_size = foot_size
        self.step_length = step_length
        self.step_width = step_width
        self.scale_zone_length = scale_zone_length
        self.path_completion = path_completion
        super().__init__(**kwargs)

    def specify_parts(self):
        self.linear_field = LinearField(length=10, direction="z+")
        self.plain_effector = PlainEffector(
            fields=[self.linear_field], scale=-1)
        self.cloner = Cloner(mode="object", target_object=self.path, offset=1 / 20, clones=[self.left_foot, self.right_foot],
                             effectors=[self.plain_effector])
        self.parts += [self.linear_field, self.plain_effector, self.cloner]

    def specify_parameters(self):
        # TODO: use spherical field with plain effector to make offset work properly
        self.offset_start_parameter = UCompletion(name="OffsetStart")
        self.offset_end_parameter = UCompletion(name="OffsetEnd")
        self.foot_size_parameter = ULength(
            name="FootSize", default_value=self.foot_size)
        self.step_length_parameter = ULength(
            name="StepLength", default_value=self.step_length)
        self.step_width_parameter = ULength(
            name="StepWidth", default_value=self.step_width)
        self.scale_zone_length_parameter = ULength(
            name="ScaleZoneLength", default_value=self.scale_zone_length)
        self.path_completion_parameter = UCompletion(
            name="PathCompletion", default_value=self.path_completion)
        self.path_length_parameter = ULength(
            name="PathLength")
        self.parameters += [self.offset_start_parameter, self.offset_end_parameter, self.step_length_parameter,
                            self.step_width_parameter, self.scale_zone_length_parameter,
                            self.path_completion_parameter, self.foot_size_parameter, self.path_length_parameter]
        """
        self.floor_plane_parameter = UOptions(
            name="FloorPlane", options=["xy", "zy", "xz"], default_value=self.floor_plane)
        """

    def specify_relations(self):
        step_width_left_foot_relation = XRelation(part=self.left_foot, whole=self, desc_ids=[self.left_foot.relative_x_parameter.desc_id],
                                                  parameters=[self.step_width_parameter], formula=f"-{self.step_width_parameter.name}/2")
        step_width_right_foot_relation = XRelation(part=self.right_foot, whole=self, desc_ids=[self.right_foot.relative_x_parameter.desc_id],
                                                   parameters=[self.step_width_parameter], formula=f"{self.step_width_parameter.name}/2")
        left_foot_size_relation = XIdentity(part=self.left_foot, whole=self, desc_ids=[self.left_foot.diameter_parameter.desc_id],
                                            parameter=self.foot_size_parameter)
        right_foot_size_relation = XIdentity(part=self.right_foot, whole=self, desc_ids=[self.right_foot.diameter_parameter.desc_id],
                                             parameter=self.foot_size_parameter)
        path_length_relation = XSplineLength(spline=self.path, whole=self,
                                             parameter=self.path_length_parameter)
        step_length_relation = XIdentity(part=self.cloner, whole=self, desc_ids=[
                                         self.cloner.desc_ids["step_size"]], parameter=self.step_length_parameter)
        offset_start_relation = XIdentity(part=self.cloner, whole=self, desc_ids=[
                                          self.cloner.desc_ids["offset_start"]], parameter=self.offset_start_parameter)
        offset_end_relation = XRelation(part=self.cloner, whole=self, desc_ids=[self.cloner.desc_ids["offset_end"]], parameters=[
                                        self.offset_end_parameter], formula=f"1-{self.offset_end_parameter.name}")
        path_completion_relation = XAlignToSpline(part=self.linear_field, whole=self, spline=self.path,
                                                  completion_parameter=self.path_completion_parameter)
        scale_zone_length_relation = XIdentity(part=self.linear_field, whole=self, desc_ids=[self.linear_field.desc_ids["length"]],
                                               parameter=self.scale_zone_length_parameter)
        """
        floor_plane_h_relation = XRelation(part=self.cloner, whole=self, desc_ids=[self.cloner.desc_ids["rotation_h"]],
                                           parameters=[self.floor_plane_parameter], formula=f"if({self.floor_plane_parameter.name}==0;0;Pi/2)")
        floor_plane_p_relation = XRelation(part=self.cloner, whole=self, desc_ids=[self.cloner.desc_ids["rotation_p"]],
                                           parameters=[self.floor_plane_parameter], formula=f"if({self.floor_plane_parameter.name}==0;-Pi/2;0))")
        floor_plane_b_relation = XRelation(part=self.cloner, whole=self, desc_ids=[self.cloner.desc_ids["rotation_b"]],
                                           parameters=[self.floor_plane_parameter], formula=f"if({self.floor_plane_parameter.name}==0;0;Pi/2)")
        """
