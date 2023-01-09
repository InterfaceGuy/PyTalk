from pydeation.objects.abstract_objects import CustomObject
import pydeation.objects.effect_objects as effect_objects
from pydeation.objects.solid_objects import Extrude, Cylinder, SweepNurbs
from pydeation.objects.line_objects import Arc, Circle, Rectangle, SplineText, Spline, PySpline, EdgeSpline
from pydeation.objects.sketch_objects import Human, Fire, Footprint, GitHub
from pydeation.objects.helper_objects import *
from pydeation.objects.light_objects import Light
from pydeation.xpresso.userdata import *
from pydeation.xpresso.xpressions import *
from pydeation.animation.animation import ScalarAnimation
from pydeation.constants import *
import random
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

    def add(self, *children):
        for child in children:
            self.children.append(child)
            child.obj.InsertUnder(self.obj)

    def sort(self, key=None):
        return self.children.sort(key=key)

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
            offset = c4d.Vector(x, y, z)
            if plane == "xy":
                return c4d.Vector(radius * np.sin(phi), radius * np.cos(phi), 0) + offset
            if plane == "zy":
                return c4d.Vector(0, radius * np.cos(phi), radius * np.sin(phi)) + offset
            if plane == "xz":
                return c4d.Vector(radius * np.sin(phi), 0, radius * np.cos(phi)) + offset

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
        if deterministic:
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
    """the director object takes multiple actors (objects) and drives a specified shared animation parameter using fields"""

    def __init__(self, *actors, parameter=None, mode="domino", completion=0, domino_zone=1/3, **kwargs):
        self.actors = actors
        self.parameter = parameter
        self.mode = mode
        self.completion = completion
        self.domino_zone = domino_zone
        super().__init__(**kwargs)

    def specify_live_bounding_box_relation(self):
        """the bounding box of the director takes all targeted actors into account"""
        live_bounding_box_relation = XBoundingBox(*self.actors, target=self, width_parameter=self.width_parameter, height_parameter=self.height_parameter,
                                                  depth_parameter=self.depth_parameter, center_parameter=self.center_parameter,
                                                  center_x_parameter=self.center_x_parameter, center_y_parameter=self.center_y_parameter, center_z_parameter=self.center_z_parameter)

    def specify_parts(self):
        if self.mode == "domino":
            self.field = LinearField(direction="x-")
        elif self.mode == "random":
            self.field = RandomField()
        self.parts.append(self.field)

    def specify_parameters(self):
        if self.mode == "domino":
            self.field_length_parameter = ULength(
                name="FieldLength")
            self.domino_zone_parameter = UCompletion(
                name="DominoZone", default_value=self.domino_zone)
            self.parameters += [self.field_length_parameter, self.domino_zone_parameter]
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
        field_length_inheritance = XIdentity(part=self.field, whole=self, desc_ids=[self.field.desc_ids["length"]], parameter=self.field_length_parameter)
        field_length_relation = XRelation(part=self, whole=self, desc_ids=[self.field_length_parameter.desc_id],
                                          parameters=[self.domino_zone_parameter, self.width_parameter], formula=f"{self.domino_zone_parameter.name} * {self.width_parameter.name}")
        if self.mode == "domino":
            self.completion_relation = XRelation(part=self.field, whole=self, desc_ids=[POS_X], parameters=[self.completion_parameter, self.width_parameter, self.field_length_parameter],
                                                 formula=f"-({self.width_parameter.name}/2+{self.field_length_parameter.name})+({self.width_parameter.name}+2*{self.field_length_parameter.name})*{self.completion_parameter.name}")

    def specify_creation(self):
        creation_action = XAction(
            Movement(self.completion_parameter, (0, 1)),
            target=self, completion_parameter=self.creation_parameter, name="Creation")

    def specify_bounding_box_relations(self):
        # the director does not need prescriptive bounding box
        pass


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

    def __init__(self, distance_humans=1 / 2, border_radius=50, synthesis_height=20, **kwargs):
        self.distance_humans = distance_humans
        self.border_radius = border_radius
        self.synthesis_height = synthesis_height
        super().__init__(**kwargs)

    def specify_parts(self):
        self.border = Circle(plane="xz", creation=True, name="Border")
        self.circle_membrane = Membrane(
            self.border, color=BLACK, fill=True)
        self.circle = Group(self.border,
                            self.circle_membrane, name="Circle")
        self.left_human = Human(perspective="portrait",
                                posture="standing", on_floor=True, diameter=30)
        self.right_human = Human(
            perspective="portrait", posture="standing", on_floor=True, diameter=30)
        self.humans = Group(self.left_human, self.right_human, name="Humans")
        self.fire = PhysicalFire()
        self.symbol = GitHub(plane="xz", z=-self.border_radius/2, diameter=20)
        self.thesis = Circle(radius=2, color=BLUE, creation=True)
        self.thesis.attach_to(self.left_human, direction="top", offset=6)
        self.antithesis = Rectangle(
            height=4, width=6, color=RED, creation=True)
        self.antithesis.attach_to(self.right_human, direction="top", offset=6)
        self.synthesis = SplineText("S", height=6, creation=True)
        # self.synthesis = Cylinder(
        #    radius=2, height=6, orientation="x+", h=PI / 8)
        self.synthesis.attach_to(self.fire)
        self.thesis_morpher = effect_objects.Morpher(
            self.thesis, self.synthesis, mode="constant")
        self.antithesis_morpher = effect_objects.Morpher(
            self.antithesis, self.synthesis, mode="constant")
        self.parts += [self.circle, self.humans, self.fire, self.symbol,
                       self.thesis, self.antithesis, self.synthesis,
                       self.thesis_morpher, self.antithesis_morpher]

    def specify_parameters(self):
        self.border_radius_parameter = ULength(
            name="BorderRadius", default_value=self.border_radius)
        self.distance_humans_parameter = UCompletion(
            name="DistanceHumans", default_value=self.distance_humans)
        self.synthesis_height_parameter = ULength(
            name="SynthesisHeightParameter", default_value=0)
        self.parameters += [self.border_radius_parameter,
                            self.distance_humans_parameter,
                            self.synthesis_height_parameter]

    def specify_relations(self):
        border_radius_relation = XIdentity(part=self.border, whole=self, desc_ids=[self.border.desc_ids["radius"]],
                                           parameter=self.border_radius_parameter)
        synthesis_height_relation = XRelation(part=self.synthesis, whole=self, desc_ids=[POS_Y],
                                              parameters=[self.synthesis_height_parameter], formula=f"{self.synthesis_height_parameter.name}")
        distance_left_human_relation = XRelation(part=self.left_human, whole=self, desc_ids=[POS_X],
                                                 parameters=[self.distance_humans_parameter, self.border_radius_parameter], formula=f"-{self.distance_humans_parameter.name}*{self.border_radius_parameter.name}")
        distance_right_human_relation = XRelation(part=self.right_human, whole=self, desc_ids=[POS_X],
                                                  parameters=[self.distance_humans_parameter, self.border_radius_parameter], formula=f"{self.distance_humans_parameter.name}*{self.border_radius_parameter.name}")

    def specify_action_parameters(self):
        self.dialectic_parameter = UCompletion(
            name="DialecticParameter", default_value=0)
        self.sand_talk_parameter = UCompletion(
            name="SandTalkParameter", default_value=0)
        self.action_parameters += [self.dialectic_parameter,
                                   self.sand_talk_parameter]

    def specify_actions(self):
        dialectic_action = XAction(
            Movement(self.thesis.opacity_parameter,
                    (0, 1 / 2), part=self.thesis),
            Movement(self.antithesis.opacity_parameter,
                    (0, 1 / 2), part=self.antithesis),
            Movement(self.synthesis_height_parameter,
                     (1 / 3, 1), output=(0, self.synthesis_height)),
            Movement(self.thesis_morpher.action_parameter,
                     (0, 3 / 4), part=self.thesis_morpher),
            Movement(self.antithesis_morpher.action_parameter,
                     (0, 3 / 4), part=self.antithesis_morpher),
            target=self, completion_parameter=self.dialectic_parameter, name="Dialectic")
        sand_talk_action = XAction(
            Movement(self.symbol.creation_parameter,
                     (0, 1), part=self.symbol),
            target=self, completion_parameter=self.sand_talk_parameter, name="SandTalk")

    def specify_creation(self):
        creation_action = XAction(
            Movement(self.fire.creation_parameter,
                     (1 / 4, 1), part=self.fire),
            Movement(self.border.opacity_parameter,
                     (0, 2 / 3), part=self.border),
            Movement(self.left_human.creation_parameter,
                     (1 / 3, 2 / 3), part=self.left_human),
            Movement(self.right_human.creation_parameter,
                     (1 / 3, 2 / 3), part=self.right_human),
            Movement(self.distance_humans_parameter, (1 / 3, 2 / 3),
                     output=(1, self.distance_humans)),
            target=self, completion_parameter=self.creation_parameter, name="Creation")

    def dialectic(self, completion=1):
        """specifies the dialectic animation"""
        desc_id = self.dialectic_parameter.desc_id
        animation = ScalarAnimation(
            target=self, descriptor=desc_id, value_fin=completion)
        return animation

    def sand_talk(self, completion=1):
        """specifies the sand_talk animation"""
        desc_id = self.sand_talk_parameter.desc_id
        animation = ScalarAnimation(
            target=self, descriptor=desc_id, value_fin=completion)
        return animation


class PhysicalFire(CustomObject):
    """the physical fire used in the physical campfire object consisting of the fire sketch and a glow light"""

    def __init__(self, brightness=1, **kwargs):
        self.brightness = brightness
        super().__init__(**kwargs)

    def specify_parts(self):
        self.fire = Fire(on_floor=True)
        self.light_source = Light(
            temperature=0.1, brightness=self.brightness, visibility_type="visible", radius=30, y=4.5)
        self.parts += [self.fire, self.light_source]

    def specify_action_parameters(self):
        self.creation_parameter = UCompletion(name="Creation", default_value=0)
        self.action_parameters = [self.creation_parameter]

    def specify_creation(self):
        creation_action = XAction(
            Movement(self.fire.svg.draw_parameter, (0, 1), part=self.fire.svg),
            Movement(self.light_source.creation_parameter,
                     (1 / 2, 1), part=self.light_source),
            target=self, completion_parameter=self.creation_parameter, name="Creation")


class DigitalCampfire(CustomObject):

    def __init__(self, distance_humans=1 / 2, border_radius=50, **kwargs):
        self.distance_humans = distance_humans
        self.border_radius = border_radius
        super().__init__(**kwargs)

    def specify_parts(self):
        self.border = Circle(plane="xz")
        self.circle_membrane = Membrane(
            self.border, color=BLACK, fill=True)
        self.circle = Group(self.border,
                            self.circle_membrane, name="Circle")
        self.left_human = Human(perspective="portrait",
                                posture="standing", on_floor=True)
        self.right_human = Human(
            perspective="portrait", posture="standing", on_floor=True)
        self.humans = Group(self.left_human, self.right_human, name="Humans")
        self.digital_fire = DigitalFire(brightness=1 / 2)
        self.parts += [self.circle, self.humans, self.digital_fire]

    def specify_parameters(self):
        self.border_radius_parameter = ULength(
            name="BorderRadiusParameter", default_value=self.border_radius)
        self.distance_humans_parameter = UCompletion(
            name="DistanceHumansParameter", default_value=self.distance_humans)
        self.parameters += [self.border_radius_parameter,
                            self.distance_humans_parameter]

    def specify_relations(self):
        border_radius_relation = XIdentity(part=self.border, whole=self, desc_ids=[self.border.desc_ids["radius"]],
                                           parameter=self.border_radius_parameter)
        distance_left_human_relation = XRelation(part=self.left_human, whole=self, desc_ids=[POS_X],
                                                 parameters=[self.distance_humans_parameter, self.border_radius_parameter], formula=f"-{self.distance_humans_parameter.name}*{self.border_radius_parameter.name}")
        distance_right_human_relation = XRelation(part=self.right_human, whole=self, desc_ids=[POS_X],
                                                  parameters=[self.distance_humans_parameter, self.border_radius_parameter], formula=f"{self.distance_humans_parameter.name}*{self.border_radius_parameter.name}")

    def specify_actions(self):
        creation_action = XAction(
            Movement(self.digital_fire.creation_parameter,
                     (1 / 4, 1), part=self.digital_fire),
            Movement(self.border.draw_parameter,
                     (0, 2 / 3), part=self.border),
            Movement(self.left_human.svg.draw_parameter,
                     (1 / 3, 2 / 3), part=self.left_human.svg),
            Movement(self.right_human.svg.draw_parameter,
                     (1 / 3, 2 / 3), part=self.right_human.svg),
            Movement(self.distance_humans_parameter, (1 / 3, 2 / 3),
                     output=(1, self.distance_humans)),
            target=self, completion_parameter=self.creation_parameter, name="Creation")


class Laptop(CustomObject):
    """a minimalistic latop"""

    def __init__(self, opening_angle=PI, **kwargs):
        self.opening_angle = opening_angle
        super().__init__(**kwargs)

    def specify_parts(self):
        self.screen_border = Rectangle(plane="xz", rounding=0.1, height=9,
                                       width=16, z=-4.5, name="Screen")
        self.screen_membrane = Membrane(self.screen_border, color=BLACK)
        self.screen = Group(self.screen_border,
                            self.screen_membrane, name="Screen")
        self.body = Rectangle(plane="xz", rounding=0.1,
                              height=9, width=16, z=-4.5, name="Body")
        self.hinge = Group(self.screen, name="ScreenHinge")
        self.parts += [self.hinge, self.screen, self.body]

    def specify_parameters(self):
        self.opening_angle_parameter = UAngle(
            name="OpeningAnlgeParameter", default_value=self.opening_angle)
        self.screen_draw_parameter = UCompletion(
            name="ScreenDrawParameter")
        self.body_draw_parameter = UCompletion(
            name="BodyDrawParameter")
        self.screen_fill_parameter = UCompletion(
            name="ScreenFillParameter", default_value=1)
        self.parameters += [self.opening_angle_parameter, self.screen_draw_parameter,
                            self.body_draw_parameter, self.screen_fill_parameter]

    def specify_relations(self):
        opening_angle_relation = XRelation(part=self.hinge, whole=self, desc_ids=[ROT_P],
                                           parameters=[self.opening_angle_parameter], formula=f"-{self.opening_angle_parameter.name}")
        screen_draw_inheritance = XIdentity(part=self.screen_border, whole=self, desc_ids=[
                                            self.screen_border.draw_parameter.desc_id], parameter=self.screen_draw_parameter)
        screen_fill_inheritance = XIdentity(part=self.screen_membrane, whole=self, desc_ids=[self.screen_membrane.fill_parameter.desc_id],
                                            parameter=self.screen_fill_parameter)
        body_draw_inheritance = XIdentity(part=self.body, whole=self, desc_ids=[
            self.body.draw_parameter.desc_id], parameter=self.body_draw_parameter)

    def specify_action_parameters(self):
        self.creation_parameter = UCompletion(name="Creation", default_value=0)
        self.action_parameters = [self.creation_parameter]

    def specify_actions(self):
        creation_action = XAction(
            Movement(self.opening_angle_parameter,
                     (1 / 3, 1), output=(0, PI / 2)),
            Movement(self.screen_draw_parameter, (0, 2 / 3)),
            Movement(self.body_draw_parameter, (0, 2 / 3)),
            target=self, completion_parameter=self.creation_parameter, name="Creation")


class DigitalFire(CustomObject):
    """the digitial version of the fire used in the physical campfire object consisting of two laptops and a glow light"""

    def __init__(self, distance=2, brightness=1, **kwargs):
        self.distance = distance
        self.brightness = brightness
        super().__init__(**kwargs)

    def specify_parts(self):
        self.laptop_left = Laptop(h=-PI / 2, name="LaptopLeft")
        self.laptop_right = Laptop(h=PI / 2, name="LaptopRight")
        self.light_source = Light(
            temperature=1, brightness=self.brightness, visibility_type="inverse_volumetric", radius=30, y=4.5)
        self.parts += [self.laptop_left, self.laptop_right, self.light_source]

    def specify_parameters(self):
        self.distance_parameter = ULength(
            name="DistanceParameter")
        self.laptop_left_creation_parameter = UCompletion(
            name="LaptopLeftCreationParameter")
        self.laptop_right_creation_parameter = UCompletion(
            name="LaptopLeftCreationParameter")
        self.parameters += [self.distance_parameter,
                            self.laptop_left_creation_parameter, self.laptop_right_creation_parameter]

    def specify_relations(self):
        distance_relation_left = XRelation(part=self.laptop_left, whole=self, desc_ids=[POS_X],
                                           parameters=[self.distance_parameter], formula=f"-{self.distance_parameter.name}/2")
        distance_relation_right = XRelation(part=self.laptop_right, whole=self, desc_ids=[POS_X],
                                            parameters=[self.distance_parameter], formula=f"{self.distance_parameter.name}/2")

    def specify_action_parameters(self):
        self.creation_parameter = UCompletion(name="Creation", default_value=0)
        self.action_parameters = [self.creation_parameter]

    def specify_actions(self):
        creation_action = XAction(
            Movement(self.laptop_left.creation_parameter,
                     (0, 1), part=self.laptop_left),
            Movement(self.laptop_right.creation_parameter,
                     (0, 1), part=self.laptop_right),
            Movement(self.distance_parameter, (0, 1),
                     output=(10, self.distance)),
            Movement(self.light_source.creation_parameter,
                     (1 / 2, 1), part=self.light_source),
            target=self, completion_parameter=self.creation_parameter, name="Creation")


class ProjectLiminality(CustomObject):

    def __init__(self, lines_distance_percent=0.22, focal_height=53.125, label=True, big_circle_radius=100, small_circle_radius=62.5, circle_gap=2, **kwargs):
        self.lines_distance_percent = lines_distance_percent
        self.focal_height = focal_height
        self.label = label
        self.big_circle_radius = big_circle_radius
        self.small_circle_radius = small_circle_radius
        self.circle_gap = circle_gap
        self.specify_action_parameters()
        super().__init__(**kwargs)

    def specify_parts(self):
        self.big_circle = Circle(
            radius=self.big_circle_radius, color=BLUE, b=PI / 2, name="BigCircle", creation=True)
        self.small_circle = Circle(
            radius=self.small_circle_radius, color=RED, z=2, name="SmallCircle", creation=True)
        self.left_line = Line((0, 0, 0), (0, 0, 0), name="LeftLine")
        self.right_line = Line((0, 0, 0), (0, 0, 0), name="RigthLine")
        self.lines = Group(self.left_line, self.right_line, z=1, name="Lines")
        self.parts += [self.big_circle,
                       self.small_circle, self.lines]
        if self.label:
            self.label = Text("ProjectLiminality", y=-200)
            self.parts.append(self.label)

    def specify_parameters(self):
        self.lines_distance_percent_parameter = UCompletion(
            name="LinesDistancePercent", default_value=self.lines_distance_percent)
        self.left_line_distance_percent_parameter = UCompletion(
            name="LeftLineDistancePercent")
        self.right_line_distance_percent_parameter = UCompletion(
            name="RightLineDistancePercent")
        self.focal_height_parameter = ULength(
            name="FocalHeight", default_value=self.focal_height)
        self.small_circle_radius_parameter = ULength(
            name="SmallCircleRadius", default_value=self.small_circle_radius)
        self.small_circle_descend_parameter = UCompletion(
            name="SmallCircleDescend")
        self.parameters += [self.lines_distance_percent_parameter, self.focal_height_parameter,
                            self.left_line_distance_percent_parameter, self.right_line_distance_percent_parameter,
                            self.small_circle_radius_parameter, self.small_circle_descend_parameter]

    def specify_relations(self):
        lines_distance_percent_relation_left = XRelation(part=self, whole=self, parameters=[self.lines_distance_percent_parameter],
                                                         desc_ids=[self.left_line_distance_percent_parameter.desc_id], formula=f"1-{self.lines_distance_percent_parameter.name}/2")
        lines_distance_percent_relation_right = XRelation(part=self, whole=self, parameters=[self.lines_distance_percent_parameter],
                                                          desc_ids=[self.right_line_distance_percent_parameter.desc_id], formula=f"{self.lines_distance_percent_parameter.name}/2")
        left_line_distance_percent_relation = XAlignToSpline(part=self.left_line.start_null, whole=self,
                                                             spline=self.big_circle, completion_parameter=self.left_line_distance_percent_parameter)
        right_line_distance_percent_relation = XAlignToSpline(part=self.right_line.start_null, whole=self,
                                                              spline=self.big_circle, completion_parameter=self.right_line_distance_percent_parameter)
        focal_height_relation_left = XIdentity(part=self.left_line.end_null, whole=self,
                                               parameter=self.focal_height_parameter, desc_ids=[POS_Y])
        focal_height_relation_right = XIdentity(part=self.right_line.end_null, whole=self,
                                                parameter=self.focal_height_parameter, desc_ids=[POS_Y])
        small_circle_radius_relation = XIdentity(part=self.small_circle, whole=self, parameter=self.small_circle_radius_parameter,
                                                 desc_ids=[self.small_circle.desc_ids["radius"]])
        small_circle_height_relation = XRelation(part=self.small_circle, whole=self, parameters=[self.focal_height_parameter, self.small_circle_descend_parameter],
                                                 desc_ids=[POS_Y], formula=f"{self.focal_height_parameter.name}+(({self.big_circle_radius}-{self.circle_gap}-{self.small_circle_radius})-{self.focal_height_parameter.name})*{self.small_circle_descend_parameter.name}")

    def specify_action_parameters(self):
        self.creation_parameter = UCompletion(name="Creation", default_value=0)
        self.action_parameters = [self.creation_parameter]

    def specify_actions(self):
        creation_action = XAction(
            Movement(self.big_circle.opacity_parameter,
                     (0, 1 / 3), part=self.big_circle),
            Movement(self.left_line.creation_parameter,
                     (1 / 3, 0.55), part=self.left_line, easing="in"),
            Movement(self.right_line.creation_parameter,
                     (1 / 3, 0.55), part=self.right_line, easing="in"),
            Movement(self.small_circle.opacity_parameter,
                     (0.5, 0.7), part=self.small_circle),
            Movement(self.small_circle_radius_parameter, (0.5, 0.7),
                     output=(0, 62.5), easing="strong_out"),
            Movement(self.small_circle_descend_parameter,
                     (0.5, 0.7), easing="strong_out"),
            Movement(self.label.creation_parameter,
                     (1 / 2, 1), part=self.label, easing=False),
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
        self.border = Rectangle(name="Border", rounding=True, creation=True)
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
            text_position_relation = XRelation(part=self.label, whole=self, desc_ids=[POS_Y], parameters=[
                self.text_position_parameter, self.height_parameter, self.text_height_parameter], formula=f"if({self.text_position_parameter.name}==0;-{self.text_height_parameter.name}/2;if({self.text_position_parameter.name}==1;{self.height_parameter.name}/2+5;-{self.height_parameter.name}/2-5-{self.text_height_parameter.name}))")
            # text_size_relation = XIdentity(
            #    part=self.label, whole=self, desc_ids=[self.label.desc_ids["text_height"]], parameter=self.text_height_parameter)
        if self.symbol:
            symbol_scale_relation = XRelation(part=self.symbol, whole=self, desc_ids=[self.symbol.diameter_parameter.desc_id], parameters=[self.width_parameter, self.height_parameter, self.symbol_border_parameter],
                                              formula=f"(1-{self.symbol_border_parameter.name})*min({self.width_parameter.name};{self.height_parameter.name})")

    def specify_creation(self):
        movements = [Movement(self.border.opacity_parameter,
                              (0, 2 / 3), part=self.border)]
        if self.label:
            movements.append(
                Movement(self.label.creation_parameter, (1 / 3, 1), part=self.label))
        if self.symbol:
            movements.append(
                Movement(self.symbol.creation_parameter, (1 / 3, 1), part=self.symbol))
            creation_action = XAction(
                *movements, target=self, completion_parameter=self.creation_parameter, name="Creation")


class MonoLogosNode(Node):

    def __init__(self, text="MonoLogos", symbol=None, width=75, height=75, rounding=1, **kwargs):
        self.symbol = symbol if symbol else ProjectLiminality(label=False)
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

    def specify_creation(self):
        creation_action = XAction(
            Movement(self.path.creation_parameter,
                     (0, 1), part=self.path, easing=False),
            target=self, completion_parameter=self.creation_parameter, name="Creation")


class BiConnection(CustomObject):
    """creates a bidirectional connection using two connection objects and a middle point"""

    def __init__(self, start_object, target_object, turbulence=False, turbulence_strength=1, turbulence_axis="x", turbulence_frequency=8, arrows=False, **kwargs):
        self.start_object = start_object
        self.target_object = target_object
        self.turbulence = turbulence
        self.turbulence_strength = turbulence_strength
        self.turbulence_axis = turbulence_axis
        self.turbulence_frequency = turbulence_frequency
        self.arrows = arrows
        super().__init__(**kwargs)

    def specify_parts(self):
        self.middle_point = Null(name="MiddlePoint")
        self.start_connection = Connection(self.middle_point, self.start_object, arrow_end=self.arrows, turbulence=self.turbulence,
                                           turbulence_strength=self.turbulence_strength, turbulence_axis=self.turbulence_axis, turbulence_frequency=self.turbulence_frequency, name="StartConnection")
        self.target_connection = Connection(self.middle_point, self.target_object, arrow_end=self.arrows, turbulence=self.turbulence,
                                            turbulence_strength=self.turbulence_strength, turbulence_axis=self.turbulence_axis, turbulence_frequency=self.turbulence_frequency, name="TargetConnection")
        self.parts += [self.middle_point,
                       self.start_connection, self.target_connection]

    def specify_relations(self):
        self.middle_point_relation = XScaleBetweenPoints(
            target=self, scaled_object=self.middle_point, point_a=self.start_object, point_b=self.target_object)

    def specify_creation(self):
        creation_action = XAction(
            Movement(self.start_connection.creation_parameter,
                     (0, 1), part=self.start_connection),
            Movement(self.target_connection.creation_parameter,
                     (0, 1), part=self.target_connection),
            target=self, completion_parameter=self.creation_parameter, name="Creation")


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

    def specify_creation(self):
        creation_action = XAction(
            Movement(self.connection.creation_parameter,
                     (0, 1), part=self.connection, easing=False),
            target=self, completion_parameter=self.creation_parameter, name="Creation")


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

    def __init__(self, path=None, left_foot=None, right_foot=None, foot_size=10, step_length=20, step_width=30, scale_zone_length=3, path_completion=1, offset_start=1 / 20, offset_end=1 / 20, **kwargs):
        self.path = path
        self.left_foot = left_foot if left_foot else Footprint(
            side="left", plane="xz", creation=True)
        self.right_foot = right_foot if right_foot else Footprint(
            side="right", plane="xz", creation=True)
        self.foot_size = foot_size
        self.step_length = step_length
        self.step_width = step_width
        self.scale_zone_length = scale_zone_length
        self.path_completion = path_completion
        self.offset_start = offset_start
        self.offset_end = offset_end
        super().__init__(**kwargs)
        # manually add clones to fix parts/clones conflict concerning visibility
        self.cloner.add_clones(self.right_foot, self.left_foot)

    def specify_position_inheritance(self):
        pass
        #position_inheritance = XIdentity(part=self, whole=self.path, desc_ids=[
        #                                 self.visual_position_parameter.desc_id], parameter=self.path.center_parameter)

    def specify_parts(self):
        self.plain_effector = PlainEffector(scale=-1, spline_field=self.path)
        self.cloner = Cloner(mode="object", target_object=self.path, clones=[self.left_foot, self.right_foot],
                             effectors=[self.plain_effector])
        self.parts += [self.plain_effector,
                       self.cloner, self.right_foot, self.left_foot]

    def specify_parameters(self):
        # TODO: use spherical field with plain effector to make offset work properly
        self.offset_start_parameter = UCompletion(
            name="OffsetStart", default_value=self.offset_start)
        self.offset_end_parameter = UCompletion(
            name="OffsetEnd", default_value=self.offset_end)
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
        path_completion_relation = XRelation(part=self.plain_effector, whole=self, desc_ids=[self.plain_effector.spline_field_desc_ids["spline_field_offset"]],
                                             parameters=[self.path_completion_parameter, self.scale_zone_length_parameter, self.offset_end_parameter], formula=f"{self.scale_zone_length_parameter.name}/100-(1+{self.scale_zone_length_parameter.name}/100)*({self.path_completion_parameter.name}-{self.offset_end_parameter.name})")
        scale_zone_length_relation = XRelation(part=self.plain_effector, whole=self, desc_ids=[self.plain_effector.spline_field_desc_ids["spline_field_range_end"]],
                                               parameters=[self.scale_zone_length_parameter], formula=f"{self.scale_zone_length_parameter.name}/100")

    def specify_action_parameters(self):
        self.creation_parameter = UCompletion(name="Creation", default_value=0)
        self.action_parameters = [self.creation_parameter]

    def specify_creation(self):
        creation_action = XAction(
            Movement(self.path_completion_parameter, (0, 1), easing=False),
            target=self, completion_parameter=self.creation_parameter, name="Creation")


class Text(CustomObject):
    """creates a text object holding individual letters which can be animated using a Director"""

    def __init__(self, text, height=50, anchor="middle", writing_completion=1, fill=1, color=WHITE, **kwargs):
        self.text = text
        self.spline_text = SplineText(
            self.text, height=height, anchor=anchor, seperate_letters=True)
        self.writing_completion = writing_completion
        self.fill = fill
        self.color = color
        self.convert_spline_text_to_spline_letters()
        self.convert_spline_letters_to_custom_letters()
        super().__init__(**kwargs)

    def set_name(self, name=None):
        self.name = self.text
        self.obj.SetName(self.name)

    def convert_spline_text_to_spline_letters(self):
        # make splinetext editable into seperate characters
        self.spline_letters_hierarchy = self.spline_text.get_editable()
        # undo seperation to later safe it as hidden spline for utility (e.g.morphing)
        self.spline_text.obj[c4d.PRIM_TEXT_SEPARATE] = False
        self.spline_text.obj.Remove()
        self.spline_letters = []
        for spline_letter in self.spline_letters_hierarchy.GetChildren():
            self.spline_letters.append(spline_letter)

    def convert_spline_letters_to_custom_letters(self):
        self.custom_letters = []
        for spline_letter in self.spline_letters:
            custom_letter = Letter(spline_letter, color=self.color)
            self.custom_letters.append(custom_letter)

    def specify_parts(self):
        self.writing_director = Director(
            *self.custom_letters, parameter=self.custom_letters[0].creation_parameter)
        self.spline_text = HelperSpline(self.spline_text.get_editable())
        self.parts += [*self.custom_letters,
                       self.writing_director, self.spline_text]

    def specify_parameters(self):
        self.writing_completion_parameter = UCompletion(
            name="WritingParameter", default_value=self.writing_completion)
        self.fill_parameter = UCompletion(name="Fill", default_value=self.fill)
        self.parameters += [self.writing_completion_parameter,
                            self.fill_parameter]

    def specify_relations(self):
        writing_completion_relation = XIdentity(part=self.writing_director, whole=self, desc_ids=[self.writing_director.completion_parameter.desc_id],
                                                parameter=self.writing_completion_parameter)

    def specify_creation(self):
        creation_action = XAction(
            Movement(self.writing_completion_parameter, (0, 1)),
            target=self, completion_parameter=self.creation_parameter, name="Creation")


class Letter(CustomObject):
    """a letter used to create text"""

    def __init__(self, character=None, draw=1, fill=1, color=WHITE, **kwargs):
        self.character = character
        self.draw = draw
        self.fill = fill
        self.color = color
        super().__init__(**kwargs)

    def specify_parts(self):
        self.spline = PySpline(self.character, color=self.color, name="Spline")
        self.membrane = Membrane(self.spline, color=self.color)
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

    def specify_creation(self):
        creation_action = XAction(
            Movement(self.draw_parameter, (0, 2 / 3)),
            Movement(self.fill_parameter, (1 / 2, 1)),
            target=self, completion_parameter=self.creation_parameter, name="Creation")


class Membrane(CustomObject):
    """creates a membrane for any given spline using the extrude and mospline object"""

    def __init__(self, spline, thickness=0, fill=0, color=WHITE, **kwargs):
        self.spline = spline
        self.thickness = thickness
        self.fill = fill
        self.color = color
        super().__init__(**kwargs)

    def specify_parts(self):
        self.mospline = MoSpline(source_spline=self.spline)
        self.extrude = Extrude(self.mospline, color=self.color)
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
        mospline_correction = XCorrectMoSplineTransform(
            self.mospline, target=self)

    def specify_creation(self):
        creation_action = XAction(
            Movement(self.fill_parameter, (0, 1)),
            target=self, completion_parameter=self.creation_parameter, name="Creation")

    def fill(self, opacity):
        return self.create(opacity)

    def un_fill(self, opacity=0):
        return self.create(opacity)


class BoundingSpline(CustomObject):
    """creates a (perspective dependent) bounding spline for any given solid object using the edge spline object"""

    def __init__(self, solid_object, color=WHITE, **kwargs):
        self.solid_object = solid_object
        self.color = color
        super().__init__(**kwargs)

    def specify_parts(self):
        self.outline_spline = EdgeSpline(self.solid_object, mode="outline")
        self.curvature_spline = EdgeSpline(self.outline_spline, mode="curvature")
        self.parts += [self.outline_spline, self.curvature_spline]

    def specify_creation(self):
        creation_action = XAction(
            Movement(self.outline_spline.draw_parameter, (0, 1), part=self.outline_spline),
            Movement(self.curvature_spline.draw_parameter, (0, 1), part=self.curvature_spline),
            target=self, completion_parameter=self.creation_parameter, name="Creation")


class SolidSpline(CustomObject):
    """creates a solid "wire" object from any given spline object"""

    def __init__(self, spline_object, color=WHITE, **kwargs):
        self.spline_object = spline_object
        self.color = color
        super().__init__(**kwargs)

    def specify_parts(self):
        self.destination_spline = EmptySpline(name="DestinationSpline")
        self.mospline = MoSpline(source_spline=self.spline_object, destination_spline=self.destination_spline)
        self.profile_spline = Rectangle(height=2, width=2, name="ProfileSpline")
        self.sweep_nurbs = SweepNurbs(rail=self.destination_spline, profile=self.profile_spline, creation=True)
        self.parts = [self.sweep_nurbs, self.mospline, self.destination_spline, self.profile_spline]

    def specify_parameters(self):
        self.glow_parameter = UCompletion(name="Glow", default_value=0)
        self.parameters += [self.glow_parameter]

    def specify_relations(self):
        glow_inheritance = XIdentity(part=self.sweep_nurbs, whole=self, desc_ids=[self.sweep_nurbs.glow_parameter.desc_id],
                                     parameter=self.glow_parameter)
        spline_correction = XCorrectMoSplineTransform(
            self.mospline, target=self)

    def glow(self, completion=1):
        """specifies the glow animation"""
        desc_id = self.glow_parameter.desc_id
        animation = ScalarAnimation(
            target=self, descriptor=desc_id, value_fin=completion)
        self.obj[desc_id] = completion
        return animation

    def unglow(self, completion=0):
        """specifies the unglow animation"""
        desc_id = self.glow_parameter.desc_id
        animation = ScalarAnimation(
            target=self, descriptor=desc_id, value_fin=completion)
        self.obj[desc_id] = completion
        return animation


class CloneConnector(CustomObject):
    """creates splines between clones of input matrices based on proximity"""

    def __init__(self, *matrices, neighbour_count=5, max_distance=500, color=WHITE, **kwargs):
        self.matrices = matrices
        self.neighbour_count = neighbour_count
        self.max_distance = max_distance
        self.color = color
        super().__init__(**kwargs)

    def specify_parts(self):
        self.spline_cache = Spline(name="SplineCache")
        self.parts += [self.spline_cache]

    def specify_parameters(self):
        self.neighbour_count_parameter = UCount(
            name="NeighbourCount", default_value=self.neighbour_count)
        self.max_distance_parameter = ULength(
            name="MaxDistance", default_value=self.max_distance)
        self.parameters += [self.neighbour_count_parameter, self.max_distance_parameter]

    def specify_relations(self):
        connect_nearest_clones = XConnectNearestClones(*self.matrices, neighbour_count_parameter=self.neighbour_count_parameter, max_distance_parameter=self.max_distance_parameter, target=self)

    def specify_creation(self):
        creation_action = XAction(
            Movement(self.spline_cache.draw_parameter, (0, 1), part=self.spline_cache),
            target=self, completion_parameter=self.creation_parameter, name="Creation")