from abc import ABC, abstractmethod
from pydeation.constants import WHITE
import c4d


class Material(ABC):

    def __init__(self, name=None):
        self.name = name
        self.document = c4d.documents.GetActiveDocument()  # get document
        self.linked_tag = None  # define attribute for tag
        self.specify_material_type()
        self.insert_to_document()
        self.set_name()
        self.set_unique_desc_ids()

    def __repr__(self):
        """sets the string representation for printing"""
        return f"{self.__class__.__name__} of {self.linked_tag.linked_object}"

    def insert_to_document(self):
        self.document.InsertMaterial(self.obj)

    def set_name(self):
        if self.name:
            self.obj.SetName(self.name)

    @abstractmethod
    def specify_material_type(self):
        pass

    @abstractmethod
    def set_material_properties(self):
        pass


class SketchMaterial(Material):

    def __init__(self, color=WHITE, arrow_start=False, arrow_end=False, **kwargs):
        self.color = color
        self.arrow_start = arrow_start
        self.arrow_end = arrow_end
        super().__init__(**kwargs)
        self.set_material_properties()

    def specify_material_type(self):
        self.obj = c4d.BaseMaterial(1011014)  # create sketch material

    def set_material_properties(self):
        # set properties
        self.obj[c4d.OUTLINEMAT_COLOR] = self.color
        if self.arrow_start:
            self.obj[c4d.OUTLINEMAT_LINESTART] = 4
        if self.arrow_end:
            self.obj[c4d.OUTLINEMAT_LINEEND] = 4
        # set constants
        self.obj[c4d.OUTLINEMAT_STARTCAP_WIDTH] = 7
        self.obj[c4d.OUTLINEMAT_STARTCAP_HEIGHT] = 5
        self.obj[c4d.OUTLINEMAT_ENDCAP_WIDTH] = 7
        self.obj[c4d.OUTLINEMAT_ENDCAP_HEIGHT] = 5
        self.obj[c4d.OUTLINEMAT_ANIMATE_AUTODRAW] = True  # draw mode
        # draw speed to completion
        self.obj[c4d.OUTLINEMAT_ANIMATE_STROKE_SPEED_TYPE] = 2
        # strokes independent of screen
        self.obj[c4d.OUTLINEMAT_STOKECLIP_TOSCREEN] = False

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "draw_completion": c4d.DescID(c4d.DescLevel(c4d.OUTLINEMAT_ANIMATE_STROKE_SPEED_COMPLETE, c4d.DTYPE_REAL, 0)),
            "opacity": c4d.DescID(c4d.DescLevel(c4d.OUTLINEMAT_OPACITY, c4d.DTYPE_REAL, 0))
        }


class FillMaterial(Material):

    def __init__(self, fill=0, color=WHITE, **kwargs):
        self.fill = fill
        self.color = color
        super().__init__(**kwargs)
        self.set_material_properties()

    def specify_material_type(self):
        self.obj = c4d.BaseMaterial(c4d.Mmaterial)  # create fill material

    def set_material_properties(self):
        # set properties
        self.obj[c4d.MATERIAL_LUMINANCE_COLOR] = self.color
        self.obj[c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS] = 1 - self.fill
        # set constants
        self.obj[c4d.MATERIAL_USE_REFLECTION] = False
        self.obj[c4d.MATERIAL_USE_COLOR] = False
        self.obj[c4d.MATERIAL_USE_LUMINANCE] = True
        self.obj[c4d.MATERIAL_USE_TRANSPARENCY] = True
        self.obj[c4d.MATERIAL_TRANSPARENCY_REFRACTION] = 1

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "transparency": c4d.DescID(c4d.DescLevel(c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS, c4d.DTYPE_REAL, 0))
        }
