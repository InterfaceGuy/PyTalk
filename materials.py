from abc import ABC, abstractmethod
from pydeation.constants import WHITE
import c4d


class Material(ABC):

    def __init__(self):
        self.document = c4d.documents.GetActiveDocument()  # get document
        self.linked_tag = None  # define attribute for tag
        self.specify_material_type()
        self.insert_to_document()

    def __repr__(self):
        """sets the string representation for printing"""
        return f"{self.__class__.__name__} of {self.linked_tag.linked_object}"

    def insert_to_document(self):
        self.document.InsertMaterial(self.obj)

    def set_name(self, name):
        self.obj.SetName(name)

    @abstractmethod
    def specify_material_type(self):
        pass

    @abstractmethod
    def set_material_properties(self):
        pass


class SketchMaterial(Material):

    def specify_material_type(self):
        self.obj = c4d.BaseMaterial(1011014)  # create sketch material

    def set_material_properties(self, color=WHITE, arrow_start=False, arrow_end=False):
        # set properties
        self.color = color
        self.obj[c4d.OUTLINEMAT_COLOR] = self.color
        if arrow_start:
            self.obj[c4d.OUTLINEMAT_LINESTART] = 4
        if arrow_end:
            self.obj[c4d.OUTLINEMAT_LINEEND] = 4
        # set constants
        self.obj[c4d.OUTLINEMAT_STARTCAP_WIDTH] = 7
        self.obj[c4d.OUTLINEMAT_STARTCAP_HEIGHT] = 5
        self.obj[c4d.OUTLINEMAT_ENDCAP_WIDTH] = 7
        self.obj[c4d.OUTLINEMAT_ENDCAP_HEIGHT] = 5
        # strokes independent of screen
        self.obj[c4d.OUTLINEMAT_STOKECLIP_TOSCREEN] = False


class FillMaterial(Material):

    def specify_material_type(self):
        self.obj = c4d.BaseMaterial(c4d.Mmaterial)  # create fill material

    def set_material_properties(self, filling=0, color=WHITE):
        # set properties
        self.color = color
        self.obj[c4d.MATERIAL_LUMINANCE_COLOR] = self.color
        self.obj[c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS] = 1 - filling
        # set constants
        self.obj[c4d.MATERIAL_USE_REFLECTION] = False
        self.obj[c4d.MATERIAL_USE_COLOR] = False
        self.obj[c4d.MATERIAL_USE_LUMINANCE] = True
        self.obj[c4d.MATERIAL_USE_TRANSPARENCY] = True
        self.obj[c4d.MATERIAL_TRANSPARENCY_REFRACTION] = 1
