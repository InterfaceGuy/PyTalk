from pydeation.materials import FillMaterial, SketchMaterial
from pydeation.tags import FillTag, SketchTag, XPressoTag
from pydeation.constants import WHITE, SCALE_X, SCALE_Y, SCALE_Z
from pydeation.animation.object_animators import Show, Hide
from pydeation.animation.sketch_animators import Draw
from pydeation.xpresso.userdata import UGroup, ULength, UCheckBox, UVector, UCompletion
from pydeation.xpresso.xpressions import XRelation, XIdentity, XSplineLength, XBoundingBox
from abc import ABC, abstractmethod
import c4d


class ProtoObject(ABC):

    def __init__(self, name=None, x=0, y=0, z=0, h=0, p=0, b=0, scale=1, scale_x=1, scale_y=1, scale_z=1, position=None, rotation=None):
        self.document = c4d.documents.GetActiveDocument()  # get document
        self.specify_object()
        self.set_unique_desc_ids()
        self.insert_to_document()
        self.set_name(name=name)
        self.set_position(x=x, y=y, z=z, position=position)
        self.set_rotation(h=h, p=p, b=b, rotation=rotation)
        self.set_scale(uniform_scale=scale, x=scale_x, y=scale_y, z=scale_z)
        self.set_object_properties()
        self.xpressions = {}  # keeps track of animators, composers etc.
        self.accessed_parameters = {}  # keeps track which parameters have AccessControl
        self.helper_objects = {}  # keeps track of helper objects created by Animators
        self.parent = None

    def __repr__(self):
        """sets the string representation for printing"""
        return self.name

    @abstractmethod
    def specify_object(self):
        pass

    def set_unique_desc_ids(self):
        """optional method to make unique descIds easily accessible"""
        pass

    def set_name(self, name=None):
        if name is None:
            self.name = self.__class__.__name__
        else:
            self.name = name
        self.obj.SetName(self.name)

    def set_position(self, x=0, y=0, z=0, position=None):
        if position is None:
            position = c4d.Vector(x, y, z)
        elif type(position) is not c4d.Vector:
            position = c4d.Vector(*position)
        self.obj[c4d.ID_BASEOBJECT_POSITION] = position

    def set_rotation(self, h=0, p=0, b=0, rotation=None):
        if rotation is None:
            rotation = c4d.Vector(h, p, b)
        elif type(rotation) is not c4d.Vector:
            rotation = c4d.Vector(*rotation)
        self.obj[c4d.ID_BASEOBJECT_ROTATION] = rotation

    def set_frozen_rotation(self, h=0, p=0, b=0, rotation=None):
        if rotation is None:
            rotation = c4d.Vector(h, p, b)
        self.obj[c4d.ID_BASEOBJECT_FROZEN_ROTATION] = rotation

    def set_scale(self, uniform_scale=1, x=1, y=1, z=1):
        if x != 1 or y != 1 or z != 1:
            scale = c4d.Vector(x, y, z)
        else:
            scale = c4d.Vector(uniform_scale, uniform_scale, uniform_scale)
        self.obj[c4d.ID_BASEOBJECT_SCALE] = scale

    def move(self, x=None, y=None, z=None, position=None):
        if position is None:
            position = c4d.Vector(x, y, z)
        elif type(position) is not c4d.Vector:
            position = c4d.Vector(*position)
        self.obj[c4d.ID_BASEOBJECT_POSITION] += position

    def rotate(self, h=None, p=None, b=None):
        if h is not None:
            self.obj[c4d.ID_BASEOBJECT_ROTATION, c4d.VECTOR_X] += h
        if p is not None:
            self.obj[c4d.ID_BASEOBJECT_ROTATION, c4d.VECTOR_Y] += p
        if b is not None:
            self.obj[c4d.ID_BASEOBJECT_ROTATION, c4d.VECTOR_Z] += b

    def scale(self, uniform_scale=None, x=None, y=None, z=None):
        if x is not None:
            self.obj[c4d.ID_BASEOBJECT_SCALE, c4d.VECTOR_X] += x
        if y is not None:
            self.obj[c4d.ID_BASEOBJECT_SCALE, c4d.VECTOR_Y] += y
        if z is not None:
            self.obj[c4d.ID_BASEOBJECT_SCALE, c4d.VECTOR_Z] += z
        if uniform_scale is not None:
            scale = c4d.Vector(uniform_scale, uniform_scale, uniform_scale)
        self.obj[c4d.ID_BASEOBJECT_SCALE] = scale

    def insert_to_document(self):
        self.document.InsertObject(self.obj)

    def create(self):
        """optionally holds a creation animation, Draw by default"""
        return Draw(self)

    def un_create(self):
        """optionally holds a uncreation animation, UnDraw by default"""
        return UnDraw(self)

    def set_object_properties(self):
        """used to set the unique properties of a specific object"""
        pass


class VisibleObject(ProtoObject):  # visible objects

    def __init__(self, visible=True, **kwargs):
        super().__init__(**kwargs)
        self.visible = visible
        self.set_visibility()
        self.set_xpresso_tags()
        self.specify_visibility_parameter()
        self.insert_visibility_parameter()
        self.specify_visibility_relation()
        self.specify_live_bounding_box_parameters()
        self.insert_live_bounding_box_parameters()
        self.specify_live_bounding_box_relation()
        self.add_bounding_box_information()
        self.specify_visual_position_parameter()

    def specify_visual_position_parameter(self):
        self.visual_position_parameter = UVector(name="VisualPosition")
        self.visual_position_u_group = UGroup(
            self.visual_position_parameter, target=self.obj, name="VisualPosition")

    def set_visibility(self):
        if self.visible:
            show_animation = Show(self)
            show_animation.execute()
        else:
            hide_animation = Hide(self)
            hide_animation.execute()

    def set_xpresso_tags(self):
        """initializes the necessary xpresso tags on the object"""
        # the composition tags hold the hierarchy of compositions and ensure execution from highest to lowest
        self.composition_tags = []
        # the animator tag holds the acting of the animators on the actual parameters
        # set priority to be executed last
        self.animator_tag = XPressoTag(
            target=self, name="AnimatorTag", priority=1, priority_mode="expression")
        # the freeze tag holds the freezing xpressions that are executed before the animators
        # set priority to be executed after compositions and before animators
        self.freeze_tag = XPressoTag(
            target=self, name="FreezeTag", priority=0, priority_mode="animation")
        # inserts an xpresso tag used for custom xpressions
        self.custom_tag = XPressoTag(target=self, name="CustomTag")

    def add_composition_tag(self):
        """adds another layer to the composition hierarchy"""
        # set priority according to position in composition hierarchy
        tag_name = "CompositionTag" + str(len(self.composition_tags))
        tag_priority = -len(self.composition_tags)
        composition_tag = XPressoTag(
            target=self, name=tag_name, priority=tag_priority, priority_mode="initial")
        self.composition_tags.append(composition_tag)
        return composition_tag.obj

    def get_clone(self):
        """clones an object and inserts it into the scene"""
        clone = self.obj.GetClone()
        self.document.InsertObject(clone)
        return clone

    def get_editable(self):
        """returns an editable clone of the object"""
        clone = self.get_clone()
        editable_clone = c4d.utils.SendModelingCommand(command=c4d.MCOMMAND_MAKEEDITABLE, list=[
            clone], mode=c4d.MODELINGCOMMANDMODE_ALL, doc=self.document)[0]
        return editable_clone

    def get_segment_count(self):
        editable_clone = self.get_editable()
        segment_count = editable_clone.GetSegmentCount() + 1  # shift to natural count
        return segment_count

    def attach_to(self, target, direction="front", offset=0):
        """places the object such that the bounding boxes touch along a given direction and makes object child of target"""
        bounding_box = self.obj.GetRad()
        bounding_box_position = self.obj.GetMp()
        bounding_box_target = target.obj.GetRad()
        bounding_box_position_target = target.obj.GetMp()
        new_position = bounding_box_position_target - bounding_box_position
        if direction == "top":
            new_position.y += bounding_box_target.y + bounding_box.y + offset
        if direction == "bottom":
            new_position.y -= bounding_box_target.y + bounding_box.y + offset
        if direction == "left":
            new_position.x -= bounding_box_target.x + bounding_box.x + offset
        if direction == "right":
            new_position.x += bounding_box_target.x + bounding_box.x + offset
        if direction == "front":
            new_position.z -= bounding_box_target.z + bounding_box.z + offset
        if direction == "back":
            new_position.z += bounding_box_target.z + bounding_box.z + offset
        self.obj.InsertUnder(target.obj)
        self.set_position(position=new_position)

    def specify_visibility_parameter(self):
        """specifies visibility parameter"""
        self.visibility_parameter = UCheckBox(
            name="Visibility", default_value=self.visible)

    def insert_visibility_parameter(self):
        """inserts the visibility parameter as userdata"""
        self.visibility_u_group = UGroup(
            self.visibility_parameter, target=self.obj, name="Visibility")

    def specify_visibility_relation(self):
        """link parameter to visibility"""
        visibility_relation = XRelation(part=self, whole=self, desc_ids=[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR, c4d.ID_BASEOBJECT_VISIBILITY_RENDER],
                                        parameters=[self.visibility_parameter], formula=f"1-{self.visibility_parameter.name}")

    def specify_live_bounding_box_parameters(self):
        """specifies bounding box parameters"""
        self.width_parameter = ULength(name="Width")
        self.height_parameter = ULength(name="Height")
        self.depth_parameter = ULength(name="Depth")
        self.center_parameter = UVector(name="Center")
        self.live_bounding_box_parameters = [
            self.width_parameter, self.height_parameter, self.depth_parameter, self.center_parameter]

    def insert_live_bounding_box_parameters(self):
        """inserts the bounding box parameters as userdata"""
        self.live_bounding_box_u_group = UGroup(
            *self.live_bounding_box_parameters, target=self.obj, name="LiveBoundingBox")

    def specify_live_bounding_box_relation(self):
        """feed bounding box information into parameters"""
        live_bounding_box_relation = XBoundingBox(self, target=self, width_parameter=self.width_parameter, height_parameter=self.height_parameter,
                                                  depth_parameter=self.depth_parameter, center_parameter=self.center_parameter)

    def add_bounding_box_information(self):
        bounding_box_center, bounding_radius = c4d.utils.GetBBox(
            self.obj, self.obj.GetMg())
        self.width = bounding_radius.x * 2
        self.height = bounding_radius.y * 2
        self.depth = bounding_radius.z * 2
        self.center = bounding_box_center


class LineObject(VisibleObject):
    """line objects consist of splines and only require a sketch material"""

    def __init__(self, color=WHITE, plane="xy", arrow_start=False, arrow_end=False, draw_completion=0, **kwargs):
        self.color = color
        self.plane = plane
        self.arrow_start = arrow_start
        self.arrow_end = arrow_end
        self.draw_completion = draw_completion
        super().__init__(**kwargs)
        self.set_sketch_material()
        self.set_sketch_tag()
        self.set_plane()
        self.spline_length_parameter_setup()
        self.draw_parameter_setup()

    def spline_length_parameter_setup(self):
        self.specify_spline_length_parameter()
        self.insert_spline_length_parameter()
        self.specify_spline_length_relation()

    def draw_parameter_setup(self):
        self.specify_draw_parameter()
        self.insert_draw_parameter()
        self.specify_draw_relation()

    def set_sketch_material(self):
        self.sketch_material = SketchMaterial(
            name=self.name, color=self.color, arrow_start=self.arrow_start, arrow_end=self.arrow_end)

    def set_sketch_tag(self):
        self.sketch_tag = SketchTag(target=self, material=self.sketch_material)

    def specify_draw_parameter(self):
        self.draw_parameter = UCompletion(
            name="Draw", default_value=self.draw_completion)

    def insert_draw_parameter(self):
        self.draw_u_group = UGroup(
            self.draw_parameter, target=self.obj, name="Sketch")

    def specify_draw_relation(self):
        self.draw_relation = XIdentity(part=self.sketch_material, whole=self, desc_ids=[self.sketch_material.desc_ids["draw_completion"]],
                                       parameter=self.draw_parameter)

    def set_plane(self):
        planes = {"xy": 0, "zy": 1, "xz": 2}
        self.obj[c4d.PRIM_PLANE] = planes[self.plane]

    def specify_spline_length_parameter(self):
        self.spline_length_parameter = ULength(name="SplineLength")

    def insert_spline_length_parameter(self):
        self.spline_length_u_group = UGroup(
            self.spline_length_parameter, target=self.obj, name="Spline")

    def specify_spline_length_relation(self):
        self.spline_length_relation = XSplineLength(
            spline=self, whole=self, parameter=self.spline_length_parameter)


class SolidObject(VisibleObject):
    """solid objects only require a fill material"""

    def __init__(self, fill=0, fill_color=WHITE, **kwargs):
        self.fill = fill
        self.fill_color = fill_color
        super().__init__(**kwargs)
        self.set_fill_material()
        self.set_fill_tag()
        self.fill_parameter_setup()

    def fill_parameter_setup(self):
        self.specify_fill_parameter()
        self.insert_fill_parameter()
        self.specify_fill_relation()

    def set_fill_material(self):
        self.fill_material = FillMaterial(
            name=self.name, fill=self.fill, color=self.fill_color)

    def set_fill_tag(self):
        self.fill_tag = FillTag(target=self, material=self.fill_material)

    def specify_fill_parameter(self):
        self.fill_parameter = UCompletion(name="Fill", default_value=self.fill)

    def insert_fill_parameter(self):
        self.fill_u_group = UGroup(
            self.fill_parameter, target=self.obj, name="Solid")

    def specify_fill_relation(self):
        self.fill_relation = XRelation(part=self.fill_material, whole=self, desc_ids=[self.fill_material.desc_ids["transparency"]],
                                       parameters=[self.fill_parameter], formula=f"1-{self.fill_parameter.name}")


class Loft(SolidObject):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Oloft)


class CustomObject(VisibleObject):
    """this class is used to create custom objects that are basically
    groups with coupling of the childrens parameters through xpresso
    GOALS:
        - recursively combine custom objects --> chain xpresso animators somehow
        - specify animation behaviour for Create/UnCreate animator"""

    def __init__(self, diameter=None, **kwargs):
        super().__init__(**kwargs)
        self.diameter = diameter
        self.parameters = []
        self.parts = []
        self.action_parameters = []
        self.specify_parts()
        self.insert_parts()
        self.specify_parameters()
        self.insert_parameters()
        self.specify_action_parameters()
        self.insert_action_parameters()
        self.specify_relations()
        self.specify_actions()
        self.add_bounding_box_information()
        self.specify_bounding_box_parameters()
        self.insert_bounding_box_parameters()
        self.specify_bounding_box_relations()
        self.specify_visibility_inheritance_relations()
        self.specify_position_inheritance()

    def specify_position_inheritance(self):
        """used to specify how the position should be determined"""
        pass

    @abstractmethod
    def specify_parts(self):
        """save parts as attributes and write them to self.parts"""
        pass

    def insert_parts(self):
        """inserts the parts as children"""
        for part in self.parts:
            # check if part is not already child so existing hierarchies won't be disturbed
            if not part.obj.GetUp():
                part.obj.InsertUnder(self.obj)
                part.parent = self

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Onull)

    def specify_parameters(self):
        """specifies optional parameters for the custom object"""
        pass

    def insert_parameters(self):
        """inserts the specified parameters as userdata"""
        if self.parameters:
            self.parameters_u_group = UGroup(
                *self.parameters, target=self.obj, name=self.name + "Parameters")

    def specify_action_parameters(self):
        """specifies optional parameters for the custom object"""
        pass

    def insert_action_parameters(self):
        """inserts the specified action_parameters as userdata"""
        if self.action_parameters:
            self.actions_u_group = UGroup(
                *self.action_parameters, target=self.obj, name=self.name + "Actions")

    def specify_relations(self):
        """specifies the relations between the part's parameters using xpresso"""
        pass

    def specify_actions(self):
        """specifies actions that coordinate parameters"""
        pass

    def specify_visibility_inheritance_relations(self):
        """inherits visibility to parts"""
        visibility_relations = []
        for part in self.parts:
            if hasattr(part, "visibility_parameter"):
                visibility_relation = XIdentity(
                    part=part, whole=self, desc_ids=[part.visibility_parameter.desc_id], parameter=self.visibility_parameter)
                visibility_relations.append(visibility_relation)

    def specify_bounding_box_parameters(self):
        """specifies bounding box parameters"""
        default_diameter = self.diameter if self.diameter else max(
            self.width, self.height, self.depth)
        self.diameter_parameter = ULength(
            name="Diameter", default_value=default_diameter)
        self.default_width_parameter = ULength(
            name="DefaultWidth", default_value=self.width)
        self.default_height_parameter = ULength(
            name="DefaultHeight", default_value=self.height)
        self.default_depth_parameter = ULength(
            name="DefaultDepth", default_value=self.depth)
        self.bounding_box_parameters = [self.diameter_parameter, self.default_width_parameter,
                                        self.default_height_parameter, self.default_depth_parameter]

    def insert_bounding_box_parameters(self):
        """inserts the bounding box parameters"""
        self.bounding_box_u_group = UGroup(
            *self.bounding_box_parameters, target=self.obj, name="BoundingBox")

    def specify_bounding_box_relations(self):
        """gives the custom object basic control over the bounding box diameter"""
        diameter_relation = XRelation(part=self, whole=self, desc_ids=[SCALE_X, SCALE_Y, SCALE_Z], parameters=[self.diameter_parameter, self.default_width_parameter, self.default_height_parameter, self.default_depth_parameter],
                                      formula=f"{self.diameter_parameter.name}/max({self.default_width_parameter.name};max({self.default_height_parameter.name};{self.default_depth_parameter.name}))")

    def create(self):
        """specifies the creation animation"""
        animations = [part.create() for part in self.parts]
        return animations

    def un_create(self):
        """specifies the uncreation animation"""
        animations = []
        for part in self.parts:
            if part.un_create():
                animations.append(part.un_create())
            else:
                animations.append(UnDraw(part))
        return animations
