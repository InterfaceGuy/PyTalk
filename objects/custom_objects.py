from abc import abstractmethod
from pydeation.objects.abstract_objects import VisibleObject
from pydeation.objects.line_objects import Line, Arc
from pydeation.xpresso.userdata import UAngle, UGroup
from pydeation.xpresso.xpressions import XRelation
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
        self.specify_relations()

    def insert_parts(self):
        """inserts the parts as children"""
        for part in self.parts:
            part.obj.InsertUnder(self.obj)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Onull)

    @abstractmethod
    def specify_relations(self):
        """specifies the relations between the part's parameters using xpresso"""
        pass

    @abstractmethod
    def specify_parts(self):
        """save parts as attributes and write them to self.parts"""
        pass

    @abstractmethod
    def create():
        """specifies the creation animation"""
        pass

    @abstractmethod
    def un_create():
        """specifies the uncreation animation"""
        pass

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
        self.u_group = UGroup(self.opening_angle, target=self.obj)

    def specify_relations(self):
        upper_lid_relation = XRelation(part=self.upper_lid, whole=self, desc_id=ROT_B,
                                       parameter=self.opening_angle, formula="-OpeningAngle/2")
        lower_lid_relation = XRelation(part=self.lower_lid, whole=self, desc_id=ROT_B,
                                       parameter=self.opening_angle, formula="OpeningAngle/2")
        eyeball_start_angle_relation = XRelation(
            part=self.eyeball, whole=self, desc_id=self.eyeball.desc_ids["start_angle"], parameter=self.opening_angle, formula="-OpeningAngle/2")
        eyeball_end_angle_relation = XRelation(
            part=self.eyeball, whole=self, desc_id=self.eyeball.desc_ids["end_angle"], parameter=self.opening_angle, formula="OpeningAngle/2")

    def create(self):
        pass

    def un_create(self):
        pass
