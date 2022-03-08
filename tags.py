from abc import ABC, abstractmethod
from pydeation.constants import WHITE
import c4d

class Tag():

    def __init__(self):
        self.document = c4d.documents.GetActiveDocument()  # get document
        self.specify_tag_type()

    def set_name(self, name):
        self.obj.SetName(name)

    @abstractmethod
    def specify_tag_type(self):
        pass

    def apply_to_object(self, target):
        target.obj.InsertTag(self.obj)
        self.linked_object = target

class MaterialTag(Tag):

    def __init__(self, material):
        super().__init__()
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

    def set_tag_properties(self):
        pass

class XPressoTag(Tag):

    def specify_tag_type(self):
        self.obj = c4d.BaseTag(c4d.Texpresso)