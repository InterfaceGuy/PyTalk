from abc import abstractmethod
from pydeation.objects.abstract_objects import VisibleObject
from pydeation.tags import XPressoTag
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

    def insert_parts(self):
        """inserts the parts as children"""
        for part in self.parts:
            part.obj.InsertUnder(self.obj)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Onull)

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

    @abstractmethod
    def create_xpression():
        """specifies the xpression linking the parts together"""
        pass

    def set_xpresso_tag(self):
        """inserts an xpresso tag used for coordination of the parts"""
        self.custom_xpresso_tag = XPressoTag(target=self, name="CustomTag")
