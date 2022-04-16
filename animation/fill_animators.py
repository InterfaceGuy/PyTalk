from pydeation.animation.abstract_animators import FillAnimator
from pydeation.xpresso.userdata import *
from pydeation.constants import WHITE
import c4d

class Fill(FillAnimator):

    def __new__(cls, *objs, filling=1, **kwargs):
        cls.set_values(filling)
        return super().__new__(cls, *objs, category="constructive", **kwargs)

    @classmethod
    def specify_desc_ids(cls):
        cls.desc_ids = {
            "fill_transparency": c4d.DescID(c4d.DescLevel(c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS, c4d.DTYPE_REAL, 0))
        }

    @classmethod
    def set_values(cls, filling):
        cls.values = [filling]

    @classmethod
    def specify_xpression(cls):
            cls.parameter_name = "FillTransparency"
            cls.interpolate = True
            cls.reverse_parameter_range = True


class UnFill(Fill):

    def __new__(cls, *objs, filling=0, **kwargs):
        cls.set_values(filling)
        return super(Fill, cls).__new__(cls, *objs, category="destructive", **kwargs)


class Pulse(Fill):

    def __new__(cls, *objs, n=1, filling_lower=0, filling_upper=1, **kwargs):
        cls.set_values(n, filling_lower, filling_upper)
        return super(Fill, cls).__new__(cls, *objs, category=None, **kwargs)

    @classmethod
    def set_values(cls, n, filling_lower, filling_upper):
        cls.values = [n, filling_lower, filling_upper]

    @classmethod
    def specify_xpression(cls):
            cls.parameter_name = "FillTransparency"
            cls.udatas = [(UCount, "n"), (UStrength, "filling_lower"), (UStrength, "filling_upper")]
            cls.formula = "filling_lower + sin(n*Pi*t) * sin(n*Pi*t) * (filling_upper - filling_lower)"
            cls.reverse_parameter_range = True


class ChangeFillColorR(FillAnimator):

    def __new__(cls, *objs, color_r=1, **kwargs):
        cls.set_values(color_r)
        return super().__new__(cls, *objs, **kwargs)

    @classmethod
    def specify_desc_ids(cls):
        cls.desc_ids = {
            "filler_color_r": c4d.DescID(c4d.DescLevel(c4d.MATERIAL_LUMINANCE_COLOR, c4d.DTYPE_COLOR, 0),
                                     c4d.DescLevel(c4d.COLOR_R, c4d.DTYPE_REAL, 0))
        }

    @classmethod
    def set_values(cls, color_r):
        cls.values = [color_r]

    @classmethod
    def specify_xpression(cls):
            cls.parameter_name = "FillColorR"
            cls.interpolate = True


class ChangeFillColorG(FillAnimator):

    def __new__(cls, *objs, color_g=1, **kwargs):
        cls.set_values(color_g)
        return super().__new__(cls, *objs, **kwargs)

    @classmethod
    def specify_desc_ids(cls):
        cls.desc_ids = {
            "filler_color_g": c4d.DescID(c4d.DescLevel(c4d.MATERIAL_LUMINANCE_COLOR, c4d.DTYPE_COLOR, 0),
                                     c4d.DescLevel(c4d.COLOR_G, c4d.DTYPE_REAL, 0))
        }

    @classmethod
    def set_values(cls, color_g):
        cls.values = [color_g]

    @classmethod
    def specify_xpression(cls):
            cls.parameter_name = "FillColorG"
            cls.interpolate = True


class ChangeFillColorB(FillAnimator):

    def __new__(cls, *objs, color_b=1, **kwargs):
        cls.set_values(color_b)
        return super().__new__(cls, *objs, **kwargs)

    @classmethod
    def specify_desc_ids(cls):
        cls.desc_ids = {
            "filler_color_b": c4d.DescID(c4d.DescLevel(c4d.MATERIAL_LUMINANCE_COLOR, c4d.DTYPE_COLOR, 0),
                                     c4d.DescLevel(c4d.COLOR_B, c4d.DTYPE_REAL, 0))
        }

    @classmethod
    def set_values(cls, color_b):
        cls.values = [color_b]

    @classmethod
    def specify_xpression(cls):
            cls.parameter_name = "FillColorB"
            cls.interpolate = True
