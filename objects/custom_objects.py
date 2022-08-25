from abc import abstractmethod
from pydeation.objects.abstract_objects import CustomObject, LineObject
from pydeation.objects.solid_objects import Extrude
from pydeation.objects.line_objects import Arc, Circle, Rectangle, SplineText, Spline, PySpline
from pydeation.objects.sketch_objects import Human, Fire, Footprint
from pydeation.objects.helper_objects import *
from pydeation.xpresso.userdata import UAngle, UGroup, ULength, UOptions, UCompletion, UText, UStrength, UCount
from pydeation.xpresso.xpressions import *
from pydeation.animation.abstract_animators import AnimationGroup
from pydeation.animation.sketch_animators import Draw, UnDraw
from pydeation.tags import XPressoTag
from pydeation.constants import *
from pydeation.utils import match_indices
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
            for target_node in nodes[i + 1:]:
                # randomly choose edge direction to make it more natural
                edge = random.choice(
                    [(start_node, target_node), (target_node, start_node)])
                all_edges.append(edge)
        if not deterministic:
            random.seed(random_seed)
        selected_edges = random.sample(
            all_edges, round(len(all_edges) * completeness))
        self.connections = []
        for edge in selected_edges:
            connection = Connection(
                *edge, turbulence=turbulence)
            self.connections.append(connection)

        return Group(*self.connections, name="Connections", visible=visible)


class Director(CustomObject):
    """the multi object takes multiple actors (objects) and drives a specified shared animation parameter using fields"""

    def __init__(self, *actors, parameter=None, mode="domino", completion=0, field_length=30, **kwargs):
        self.actors = actors
        self.parameter = parameter
        self.mode = mode
        self.completion = completion
        self.field_length = field_length
        super().__init__(**kwargs)

    def specify_live_bounding_box_relation(self):
        """the bounding box of the director takes all targeted actors into account"""
        live_bounding_box_relation = XBoundingBox(*self.actors, target=self, width_parameter=self.width_parameter, height_parameter=self.height_parameter,
                                                  depth_parameter=self.depth_parameter, center_parameter=self.center_parameter)

    def specify_parts(self):
        if self.mode == "domino":
            self.field = LinearField(direction="x-")
        elif self.mode == "random":
            self.field = RandomField()
        self.parts.append(self.field)

    def specify_parameters(self):
        if self.mode == "domino":
            self.field_length_parameter = ULength(
                name="FieldLength", default_value=self.field_length)
            self.parameters.append(self.field_length_parameter)
        self.completion_parameter = type(self.parameter)(
            name=self.parameter.name, default_value=self.completion)
        self.bounding_box_max_x_parameter = ULength(name="BoundingBoxMaxX")
        self.parameters += [self.completion_parameter,
                            self.bounding_box_max_x_parameter]

    def specify_relations(self):
        field_to_parameter_relations = []
        for child in self.actors:
            field_to_parameter_relation = XLinkParamToField(
                field=self.field, target=self, part=child, parameter=self.parameter)
            field_to_parameter_relations.append(field_to_parameter_relation)
        field_length_relation = XIdentity(part=self.field, whole=self, desc_ids=[self.field.desc_ids["length"]],
                                          parameter=self.field_length_parameter)
        if self.mode == "domino":
            self.completion_relation = XRelation(part=self.field, whole=self, desc_ids=[POS_X], parameters=[self.completion_parameter, self.width_parameter, self.field_length_parameter],
                                                 formula=f"-({self.width_parameter.name}/2+{self.field_length_parameter.name})+({self.width_parameter.name}+2*{self.field_length_parameter.name})*{self.completion_parameter.name}")


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

    def __init__(self, lines_distance_percent=0.22, lines_height=53.125, lines_completion=1, big_circle_radius=100, big_circle_opacity=1, small_circle_radius=62.5, small_circle_opacity=1, circle_gap=2, show_label=True, **kwargs):
        self.lines_distance_percent = lines_distance_percent
        self.lines_height = lines_height
        self.lines_completion = lines_completion
        self.big_circle_radius = big_circle_radius
        self.big_circle_opacity = big_circle_opacity
        self.small_circle_radius = small_circle_radius
        self.small_circle_opacity = small_circle_opacity
        self.circle_gap = circle_gap
        super().__init__(**kwargs)

    def specify_parts(self):
        self.big_circle = Circle(color=BLUE, b=PI / 2, name="BigCircle")
        self.small_circle = Circle(color=RED, z=2, name="SmallCircle")
        self.left_line = Line((0, 0, 0), (0, 0, 0), name="LeftLine")
        self.right_line = Line((0, 0, 0), (0, 0, 0), name="RigthLine")
        self.lines = Group(self.left_line, self.right_line, z=1, name="Lines")
        self.label = Text("ProjectLiminality", y=-100)
        self.parts += [self.big_circle,
                       self.small_circle, self.lines, self.label]

    def specify_parameters(self):
        self.lines_distance_percent_parameter = UCompletion(
            name="LinesDistancePercent", default_value=self.lines_distance_percent)
        self.left_line_distance_percent_parameter = UCompletion(
            name="LeftLineDistancePercent")
        self.right_line_distance_percent_parameter = UCompletion(
            name="RightLineDistancePercent")
        self.lines_height_parameter = ULength(
            name="LinesHeight", default_value=self.lines_height)
        self.lines_completion_parameter = UCompletion(
            name="LinesCompletion", default_value=self.lines_completion)
        self.big_circle_radius_parameter = ULength(
            name="BigCircleRadius", default_value=self.big_circle_radius)
        self.big_circle_opacity_parameter = UCompletion(
            name="SmallCircleOpacity", default_value=self.big_circle_opacity)
        self.small_circle_radius_parameter = ULength(
            name="SmallCircleRadius", default_value=self.small_circle_radius)
        self.small_circle_opacity_parameter = UCompletion(
            name="SmallCircleOpacity", default_value=self.small_circle_opacity)
        self.circle_gap_parameter = ULength(
            name="CircleGap", default_value=self.circle_gap)
        self.parameters += [self.lines_distance_percent_parameter, self.lines_height_parameter, self.lines_completion_parameter,
                            self.right_line_distance_percent_parameter, self.left_line_distance_percent_parameter, self.big_circle_radius_parameter,
                            self.big_circle_opacity_parameter, self.small_circle_radius_parameter, self.small_circle_opacity_parameter,
                            self.circle_gap_parameter]

    def specify_relations(self):
        lines_distance_percent_relation_left = XRelation(part=self, whole=self, parameters=[self.lines_distance_percent_parameter],
                                                         desc_ids=[self.left_line_distance_percent_parameter.desc_id], formula=f"1-{self.lines_distance_percent_parameter.name}/2")
        lines_distance_percent_relation_right = XRelation(part=self, whole=self, parameters=[self.lines_distance_percent_parameter],
                                                          desc_ids=[self.right_line_distance_percent_parameter.desc_id], formula=f"{self.lines_distance_percent_parameter.name}/2")
        left_line_distance_percent_relation = XAlignToSpline(part=self.left_line.start_null, whole=self,
                                                             spline=self.big_circle, completion_parameter=self.left_line_distance_percent_parameter)
        right_line_distance_percent_relation = XAlignToSpline(part=self.right_line.start_null, whole=self,
                                                              spline=self.big_circle, completion_parameter=self.right_line_distance_percent_parameter)
        lines_height_relation_left = XIdentity(part=self.left_line.end_null, whole=self,
                                               parameter=self.lines_height_parameter, desc_ids=[POS_Y])
        lines_height_relation_right = XIdentity(part=self.right_line.end_null, whole=self,
                                                parameter=self.lines_height_parameter, desc_ids=[POS_Y])
        small_circle_height_relation = XRelation(part=self.small_circle, whole=self, parameters=[self.small_circle_radius_parameter, self.big_circle_radius_parameter, self.circle_gap_parameter],
                                                 desc_ids=[POS_Y], formula=f"{self.big_circle_radius_parameter.name}-{self.small_circle_radius_parameter.name}-{self.circle_gap_parameter.name}")
        small_circle_radius_relation = XIdentity(part=self.small_circle, whole=self, parameter=self.small_circle_radius_parameter,
                                                 desc_ids=[self.small_circle.desc_ids["radius"]])
        big_circle_radius_relation = XIdentity(part=self.big_circle, whole=self, parameter=self.big_circle_radius_parameter,
                                               desc_ids=[self.big_circle.desc_ids["radius"]])
        lines_completion_relation_left = XIdentity(part=self.left_line.connection.path.sketch_material, whole=self, parameter=self.lines_completion_parameter, desc_ids=[
                                                   self.left_line.connection.path.sketch_material.desc_ids["draw_completion"]])
        lines_completion_relation_right = XIdentity(part=self.right_line.connection.path.sketch_material, whole=self, parameter=self.lines_completion_parameter, desc_ids=[
                                                    self.right_line.connection.path.sketch_material.desc_ids["draw_completion"]])
        big_circle_opacity_relation = XIdentity(part=self.big_circle.sketch_material, whole=self, parameter=self.big_circle_opacity_parameter,
                                                desc_ids=[self.big_circle.sketch_material.desc_ids["opacity"]])
        small_circle_opacity_relation = XIdentity(part=self.small_circle.sketch_material, whole=self, parameter=self.small_circle_opacity_parameter,
                                                  desc_ids=[self.small_circle.sketch_material.desc_ids["opacity"]])

    def specify_action_parameters(self):
        self.creation_parameter = UCompletion(name="Creation", default_value=0)
        self.action_parameters = [self.creation_parameter]

    def specify_actions(self):
        creation_action = XAction(
            Movement(self.big_circle_opacity_parameter, (0, 1 / 3)),
            Movement(self.lines_completion_parameter, (1 / 3, 2 / 3)),
            Movement(self.small_circle_opacity_parameter, (2 / 3, 1)),
            Movement(self.small_circle_radius_parameter,
                     (2 / 3, 1), output=(48, 62)),
            target=self, completion_parameter=self.creation_parameter, name="Creation")


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

    def __init__(self, start_object, target_object, turbulence=False, turbulence_strength=1, turbulence_axis="x", turbulence_frequency=8, arrow_start=None, arrow_end=None, **kwargs):
        self.start_object = start_object
        self.start_object_has_border = hasattr(
            self.start_object, "border")
        self.target_object = target_object
        self.target_object_has_border = hasattr(
            self.target_object, "border")
        self.turbulence = turbulence
        self.turbulence_strength = turbulence_strength
        self.turbulence_axis = turbulence_axis
        self.turbulence_frequency = turbulence_frequency
        self.arrow_start = arrow_start
        self.arrow_end = arrow_end
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
        self.tracer = Tracer(trace_start, trace_target,
                             tracing_mode="objects", name="Tracer")
        self.path = Spline(
            name="Path", arrow_start=self.arrow_start, arrow_end=self.arrow_end)
        self.mospline = MoSpline(
            source_spline=self.tracer, point_count=self.turbulence_frequency, destination_spline=self.path)
        self.parts += [self.tracer, self.path, self.mospline]
        if self.turbulence:
            self.spherical_field = SphericalField()
            self.random_effector = RandomEffector(
                position=(0, 0, 0), fields=[self.spherical_field])
            self.mospline.add_effector(self.random_effector)
            self.parts += [self.spherical_field, self.random_effector]

    def specify_parameters(self):
        self.path_length_parameter = ULength(name="PathLength")
        self.parameters += [self.path_length_parameter]
        if self.turbulence:
            self.turbulence_strength_parameter = UStrength(
                name="TurbulenceStrength", default_value=self.turbulence_strength)
            self.turbulence_frequency_parameter = UCount(
                name="TurbulenceFrequency", default_value=self.turbulence_frequency)
            self.turbulence_axis_parameter = UOptions(name="TurbulencePlane", options=["x", "y"],
                                                      default_value=self.turbulence_axis)
            self.parameters += [self.turbulence_strength_parameter,
                                self.turbulence_frequency_parameter,
                                self.turbulence_axis_parameter]

    def specify_relations(self):
        self.path_length_relation = XIdentity(part=self, whole=self.path, desc_ids=[
                                              self.path_length_parameter.desc_id], parameter=self.path.spline_length_parameter)
        if self.turbulence:
            self.turbulence_strength_relation_x = XRelation(part=self.random_effector, whole=self, desc_ids=[self.random_effector.desc_ids["position_x"]],
                                                            parameters=[
                self.turbulence_strength_parameter, self.path_length_parameter, self.turbulence_axis_parameter],
                formula=f"if({self.turbulence_axis_parameter.name}==0;1/10*{self.path_length_parameter.name}*{self.turbulence_strength_parameter.name};0)")
            self.turbulence_strength_relation_y = XRelation(part=self.random_effector, whole=self, desc_ids=[self.random_effector.desc_ids["position_y"]],
                                                            parameters=[
                self.turbulence_strength_parameter, self.path_length_parameter, self.turbulence_axis_parameter],
                formula=f"if({self.turbulence_axis_parameter.name}==1;1/10*{self.path_length_parameter.name}*{self.turbulence_strength_parameter.name};0)")
            self.turbulence_frequency_relation = XIdentity(part=self.mospline, whole=self, desc_ids=[
                                                           self.mospline.desc_ids["point_count"]], parameter=self.turbulence_frequency_parameter)

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


class Line(CustomObject):

    def __init__(self, start_point, end_point, arrow_start=False, arrow_end=False, **kwargs):
        self.start_point = start_point
        self.end_point = end_point
        self.arrow_start = arrow_start
        self.arrow_end = arrow_end
        super().__init__(**kwargs)

    def specify_parts(self):
        self.start_null = Null(name="StartPoint", position=self.start_point)
        self.end_null = Null(name="EndPoint", position=self.end_point)
        self.connection = Connection(
            self.start_null, self.end_null, arrow_start=self.arrow_start, arrow_end=self.arrow_end)
        self.parts += [self.start_null, self.end_null, self.connection]


class Arrow(Line):

    def __init__(self, start_point, stop_point, direction="positive", **kwargs):
        if direction == "positive":
            self.arrow_start = False
            self.arrow_end = True
        elif direction == "negative":
            self.arrow_start = True
            self.arrow_end = False
        elif direction == "bidirectional":
            self.arrow_start = True
            self.arrow_end = True
        super().__init__(start_point, stop_point,
                         arrow_start=self.arrow_start, arrow_end=self.arrow_end, **kwargs)


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
        # manually add clones to fix parts/clones conflict concerning visibility
        self.cloner.add_clones(self.right_foot, self.left_foot)

    def specify_position_inheritance(self):
        position_inheritance = XIdentity(part=self, whole=self.path, desc_ids=[
                                         self.visual_position_parameter.desc_id], parameter=self.path.center_parameter)

    def specify_parts(self):
        self.linear_field = LinearField(length=10, direction="z+")
        self.plain_effector = PlainEffector(
            fields=[self.linear_field], scale=-1)
        self.cloner = Cloner(mode="object", target_object=self.path, offset=1 / 20, clones=[self.left_foot, self.right_foot],
                             effectors=[self.plain_effector])
        self.parts += [self.linear_field, self.plain_effector,
                       self.cloner, self.right_foot, self.left_foot]

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


class SplineScreen(CustomObject):
    """creates a spline at the intersection with a 2D screen"""

    def __init__(self, orientation="z+", **kwargs):
        self.orientation = orientation
        super().__init__(**kwargs)

    def specify_parts(self):
        self.screen = Plane(orientation=self.orientation)
        self.edge_spline = EdgeSpline(mode="intersection")
        self.parts += [self.edge_spline]

    def specify_parameters(self):
        self.some_parameter = UCompletion(
            name="SomeParameter", default_value=self.some_value)
        self.parameters += [self.some_parameter]

    def specify_relations(self):
        screen_width_relation = XRelation(part=self.screen, whole=self, desc_ids=[self.screen.desc_ids["width"]],
                                          parameters=[self.width_parameter], formula=f"{self.width_parameter.name}")
        screen_height_relation = XRelation(part=self.screen, whole=self, desc_ids=[self.screen.desc_ids["height"]],
                                           parameters=[self.height_parameter], formula=f"{self.height_parameter.name}")

    def specify_action_parameters(self):
        self.creation_parameter = UCompletion(name="Creation", default_value=0)
        self.action_parameters = [self.creation_parameter]

    def specify_actions(self):
        creation_action = XAction(
            Movement(self.some_parameter, (0, 1)),
            target=self, completion_parameter=self.creation_parameter, name="Creation")


class Text(CustomObject):
    """creates a text object holding individual letters which can be animated using a Director"""

    def __init__(self, text, height=50, anchor="middle", writing_completion=1, **kwargs):
        self.text = text
        self.spline_text = SplineText(
            self.text, height=height, anchor=anchor, seperate_letters=True)
        self.writing_completion = writing_completion
        self.convert_spline_text_to_spline_letters()
        self.convert_spline_letters_to_custom_letters()
        super().__init__(**kwargs)

    def convert_spline_text_to_spline_letters(self):
        self.spline_letters_hierarchy = self.spline_text.get_editable()
        self.spline_text.obj.Remove()
        self.spline_letters = []
        for spline_letter in self.spline_letters_hierarchy.GetChildren():
            self.spline_letters.append(spline_letter)

    def convert_spline_letters_to_custom_letters(self):
        self.custom_letters = []
        for spline_letter in self.spline_letters:
            custom_letter = Letter(spline_letter)
            self.custom_letters.append(custom_letter)

    def specify_parts(self):
        self.writing_director = Director(
            *self.custom_letters, parameter=self.custom_letters[0].creation_parameter)
        self.parts += [*self.custom_letters, self.writing_director]

    def specify_parameters(self):
        self.writing_completion_parameter = UCompletion(
            name="WritingParameter", default_value=self.writing_completion)
        self.parameters += [self.writing_completion_parameter]

    def specify_relations(self):
        writing_completion_relation = XIdentity(part=self.writing_director, whole=self, desc_ids=[self.writing_director.completion_parameter.desc_id],
                                                parameter=self.writing_completion_parameter)

    def specify_action_parameters(self):
        pass
        """self.creation_parameter = UCompletion(name="Creation", default_value=0)
        self.action_parameters = [self.creation_parameter]"""

    def specify_actions(self):
        pass
        """creation_action = XAction(
        Movement(self.some_parameter, (0, 1)),
        target=self, completion_parameter=self.creation_parameter, name="Creation")"""


class Letter(CustomObject):
    """a letter used to create text"""

    def __init__(self, character=None, draw=1, fill=1, **kwargs):
        self.character = character
        self.draw = draw
        self.fill = fill
        super().__init__(**kwargs)

    def specify_parts(self):
        self.spline = PySpline(self.character, name="Spline")
        self.membrane = Membrane(self.spline)
        # set global matrices
        self.obj.SetMg(self.character.GetMg())
        self.parts += [self.spline, self.membrane]

    def specify_position_inheritance(self):
        position_inheritance = XIdentity(part=self, whole=self, desc_ids=[
                                         self.visual_position_parameter.desc_id], parameter=self.center_parameter)

    def specify_parameters(self):
        self.draw_parameter = UCompletion(name="Draw", default_value=self.draw)
        self.fill_parameter = UCompletion(name="Fill", default_value=self.fill)
        self.parameters += [self.draw_parameter, self.fill_parameter]

    def specify_relations(self):
        draw_inheritance = XIdentity(part=self.spline, whole=self,
                                     desc_ids=[self.spline.draw_parameter.desc_id], parameter=self.draw_parameter)
        fill_inheritance = XIdentity(part=self.membrane, whole=self,
                                     desc_ids=[self.membrane.fill_parameter.desc_id], parameter=self.fill_parameter)
        mospline_correction = XCorrectMoSplineTransform(
            self.membrane.mospline, target=self)

    def specify_action_parameters(self):
        self.creation_parameter = UCompletion(name="Creation", default_value=0)
        self.action_parameters = [self.creation_parameter]

    def specify_actions(self):
        creation_action = XAction(
            Movement(self.draw_parameter, (0, 2 / 3)),
            Movement(self.fill_parameter, (1 / 2, 1)),
            target=self, completion_parameter=self.creation_parameter, name="Creation")


class Membrane(CustomObject):
    """creates a membrane for any given spline using the extrude and mospline object"""

    def __init__(self, spline, thickness=0, fill=0, **kwargs):
        self.spline = spline
        self.thickness = thickness
        self.fill = fill
        super().__init__(**kwargs)

    def specify_parts(self):
        self.mospline = MoSpline(source_spline=self.spline)
        self.extrude = Extrude(self.mospline)
        self.parts += [self.extrude, self.mospline]

    def specify_parameters(self):
        self.thickness_parameter = ULength(
            name="ThicknessParameter", default_value=self.thickness)
        self.fill_parameter = UCompletion(name="Fill", default_value=self.fill)
        self.parameters += [self.thickness_parameter, self.fill_parameter]

    def specify_relations(self):
        thickness_relation = XIdentity(part=self.extrude, whole=self, desc_ids=[self.extrude.desc_ids["offset"]],
                                       parameter=self.thickness_parameter)
        fill_inheritance = XIdentity(part=self.extrude, whole=self, desc_ids=[self.extrude.fill_parameter.desc_id],
                                     parameter=self.fill_parameter)

    def specify_action_parameters(self):
        pass
        #self.creation_parameter = UCompletion(name="Creation", default_value=0)
        #self.action_parameters = [self.creation_parameter]

    def specify_actions(self):
        pass
        # creation_action = XAction(
        #    Movement(self.some_parameter, (0, 1)),
        #    target=self, completion_parameter=self.creation_parameter, name="Creation")


class Morpher(CustomObject):
    """creates a (set of) spline(s) depending on segment count that morphs between any two splines"""

    def __init__(self, spline_ini: LineObject, spline_fin: LineObject, morph_completion=0, linear_field_length=50, **kwargs):
        self.spline_ini = spline_ini
        self.spline_fin = spline_fin
        self.morph_completion = morph_completion
        self.linear_field_length = linear_field_length
        self.get_segment_counts()
        super().__init__(**kwargs)

    def set_name(self, name=None):
        self.name = f"Morph:{self.spline_ini.name}->{self.spline_fin.name}"
        self.obj.SetName(self.name)

    def get_segment_counts(self):
        self.segment_count_ini = self.spline_ini.get_segment_count()
        self.segment_count_fin = self.spline_fin.get_segment_count()
        self.segment_count = max(
            self.segment_count_ini, self.segment_count_fin)

    def specify_parts(self):
        self.create_linear_field()
        self.create_spline_effectors()
        self.create_destination_splines()
        self.create_mosplines()

        self.parts += [self.linear_field, self.spline_effectors_ini,
                       self.spline_effectors_fin, self.mosplines, self.destination_splines]

    def create_linear_field(self):
        self.linear_field = LinearField(direction="x-")
        self.parts.append(self.linear_field)

    def create_spline_effectors(self):
        self.spline_effectors_ini = Group(*[SplineEffector(spline=self.spline_ini, segment_index=i, name=f"SplineEffector{i}")
                                            for i in range(self.segment_count_ini)], name="SplineEffectorsInitial")
        self.spline_effectors_fin = Group(*[SplineEffector(spline=self.spline_fin, fields=[self.linear_field], segment_index=i, name=f"SplineEffector{i}")
                                            for i in range(self.segment_count_fin)], name="SplineEffectorsFinal")

    def create_destination_splines(self):
        self.destination_splines = Group(
            *[Spline(name=f"DestinationSpline{i}", draw_completion=1) for i in range(self.segment_count)], name="DestinationSplines")

    def create_mosplines(self):
        self.mosplines = Group(*[MoSpline(source_spline=self.spline_ini, destination_spline=destination_spline, name=f"MoSpline{i}")
                                 for i, destination_spline in enumerate(self.destination_splines)], name="MoSplines")
        # we want to match the segments in the most natural way using modulu
        indices_ini, indices_fin = match_indices(
            self.segment_count_ini, self.segment_count_fin)
        for i, j, mospline in zip(indices_ini, indices_fin, self.mosplines):
            mospline.add_effector(self.spline_effectors_ini[i])
            mospline.add_effector(self.spline_effectors_fin[j])

    def specify_parameters(self):
        self.morph_completion_parameter = UCompletion(
            name="MorphCompletionParameter", default_value=self.morph_completion)
        self.linear_field_length_parameter = ULength(
            name="FieldLengthParameter", default_value=self.linear_field_length)
        self.parameters += [self.morph_completion_parameter,
                            self.linear_field_length_parameter]

    def specify_relations(self):
        morph_completion_relation = XRelation(part=self.linear_field, whole=self, desc_ids=[POS_X], parameters=[self.morph_completion_parameter, self.linear_field_length_parameter, self.width_parameter],
                                              formula=f"-({self.width_parameter.name}/2+{self.linear_field_length_parameter.name})+({self.width_parameter.name}+2*{self.linear_field_length_parameter.name})*{self.morph_completion_parameter.name}")
        linear_field_length_relation = XIdentity(part=self.linear_field, whole=self, desc_ids=[self.linear_field.desc_ids["length"]],
                                                 parameter=self.linear_field_length_parameter)

    def specify_action_parameters(self):
        pass
        """
        self.creation_parameter = UCompletion(name="Creation", default_value=0)
        self.action_parameters = [self.creation_parameter]
        """

    def specify_actions(self):
        pass
        """
        creation_action = XAction(
            Movement(self.morph_completion_parameter, (0, 1)),
            target=self, completion_parameter=self.creation_parameter, name="Creation")
        """
