from abc import ABC, abstractmethod
from pydeation.constants import WHITE
import c4d


class Tag():

    def __init__(self, target=None, name=None):
        self.document = c4d.documents.GetActiveDocument()  # get document
        self.specify_tag_type()
        self.set_tag_properties()
        self.set_name(name)
        self.apply_to_object(target)

    def set_name(self, name):
        if name:
            self.obj.SetName(name)

    @abstractmethod
    def specify_tag_type(self):
        pass

    def apply_to_object(self, target):
        target.obj.InsertTag(self.obj)
        self.linked_object = target

    def set_tag_properties(self):
        pass


class MaterialTag(Tag):

    def __init__(self, material=None, **kwargs):
        super().__init__(**kwargs)
        self.link_to_material(material)

    @ abstractmethod
    def specify_tag_type(self):
        pass

    @ abstractmethod
    def link_to_material(self):
        pass

    @ abstractmethod
    def set_tag_properties(self):
        pass


class SketchTag(MaterialTag):

    def specify_tag_type(self):
        self.obj = c4d.BaseTag(1011012)  # create sketch tag

    def link_to_material(self, material):
        self.obj[c4d.OUTLINEMAT_LINE_DEFAULT_MAT_V] = material.obj
        self.obj[c4d.OUTLINEMAT_LINE_DEFAULT_MAT_H] = material.obj
        self.linked_material = material
        material.linked_tag = self

    def set_tag_properties(self):
        self.obj[c4d.OUTLINEMAT_LINE_SPLINES] = True


class FillTag(MaterialTag):

    def specify_tag_type(self):
        self.obj = c4d.BaseTag(c4d.Ttexture)  # create fill tag

    def link_to_material(self, material):
        self.obj.SetMaterial(material.obj)
        self.linked_material = material
        material.linked_tag = self

    def set_tag_properties(self):
        pass


class XPressoTag(Tag):

    def __init__(self, priority=0, priority_mode="animation", **kwargs):
        super().__init__(**kwargs)
        self.set_priority(priority, mode=priority_mode)

    def specify_tag_type(self):
        self.obj = c4d.BaseTag(c4d.Texpresso)

    def set_priority(self, value, mode="animation"):
        # define priority modes
        modes = {
            "initial": c4d.CYCLE_INITIAL,
            "animation": c4d.CYCLE_ANIMATION,
            "expression": c4d.CYCLE_EXPRESSION
        }
        # set execution priority
        priority_data = self.obj[c4d.EXPRESSION_PRIORITY]
        # set priority value
        priority_data.SetPriorityValue(c4d.PRIORITYVALUE_PRIORITY, value)
        # set mode to initial
        priority_data.SetPriorityValue(c4d.PRIORITYVALUE_MODE, modes[mode])
        self.obj[c4d.EXPRESSION_PRIORITY] = priority_data
