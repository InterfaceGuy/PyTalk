from abc import abstractmethod
from pydeation.objects.abstract_objects import VisibleObject
from pydeation.objects.line_objects import Line, Arc, Circle, Rectangle
from pydeation.objects.svg_objects import Human, Fire
from pydeation.objects.helper_objects import Group
from pydeation.xpresso.userdata import UAngle, UGroup
from pydeation.xpresso.xpressions import XRelation
from pydeation.animation.abstract_animators import AnimationGroup
from pydeation.animation.sketch_animators import Draw, UnDraw
from pydeation.tags import XPressoTag
from pydeation.constants import *
import c4d


class CustomObject(VisibleObject):
    """this class is used to create custom objects that are basically
    groups with coupling of the childrens parameters through xpresso
    GOALS:
        - recursively combine custom objects --> chain xpresso animators somehow
        - specify animation behaviour for Create/UnCreate animator"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.specify_parts()
        self.insert_parts()
        self.set_xpresso_tag()
        self.specify_parameters()
        self.insert_parameters()
        self.specify_relations()

    def insert_parts(self):
        """inserts the parts as children"""
        for part in self.parts:
            part.obj.InsertUnder(self.obj)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Onull)

    def specify_parameters(self):
        """specifies optional parameters for the custom object"""
        self.parameters = None

    def insert_parameters(self):
        """inserts the specified parameters as userdata"""
        if self.parameters:
            self.u_group = UGroup(
                *self.parameters, target=self.obj, name=self.name)

    def specify_relations(self):
        """specifies the relations between the part's parameters using xpresso"""
        pass

    @abstractmethod
    def specify_parts(self):
        """save parts as attributes and write them to self.parts"""
        pass

    def create(self):
        """specifies the creation animation"""
        animations = AnimationGroup(*[part.create() for part in self.parts])
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

    def set_xpresso_tag(self):
        """inserts an xpresso tag used for coordination of the parts"""
        self.custom_tag = XPressoTag(target=self, name="CustomTag")


class Eye(CustomObject):

    def specify_parts(self):
        self.upper_lid = Line((0, 0, 0), (200, 0, 0), name="UpperLid")
        self.lower_lid = Line((0, 0, 0), (200, 0, 0), name="LowerLid")
        self.eyeball = Arc(name="Eyeball")
        self.parts = [self.upper_lid, self.lower_lid, self.eyeball]

    def specify_parameters(self):
        self.opening_angle = UAngle(name="OpeningAngle")
        self.parameters = [self.opening_angle]

    def specify_relations(self):
        upper_lid_relation = XRelation(part=self.upper_lid, whole=self, desc_id=ROT_B,
                                       parameter=self.opening_angle, formula="-OpeningAngle/2")
        lower_lid_relation = XRelation(part=self.lower_lid, whole=self, desc_id=ROT_B,
                                       parameter=self.opening_angle, formula="OpeningAngle/2")
        eyeball_start_angle_relation = XRelation(
            part=self.eyeball, whole=self, desc_id=self.eyeball.desc_ids["start_angle"], parameter=self.opening_angle, formula="-OpeningAngle/2")
        eyeball_end_angle_relation = XRelation(
            part=self.eyeball, whole=self, desc_id=self.eyeball.desc_ids["end_angle"], parameter=self.opening_angle, formula="OpeningAngle/2")


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
        self.parts = [self.circle, self.humans, self.fire, self.symbol]


class ProjectLiminality(CustomObject):

    def specify_parts(self):
        self.big_circle = Circle(radius=100, color=BLUE)
        self.small_circle = Circle(radius=50, y=50, color=RED)
        self.left_line = Line((-70, -50, 0), (0, 50, 0))
        self.right_line = Line((70, -50, 0), (0, 50, 0))
        self.lines = Group(self.left_line, self.right_line, name="Lines")
        self.parts = [self.big_circle, self.small_circle, self.lines]
