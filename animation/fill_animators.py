from pydeation.animation.abstract_animators import FillAnimator
from pydeation.xpresso.userdata import *
import c4d

class Fill(FillAnimator):

    def __new__(cls, *objs, filling=1, **kwargs):
        cls.set_values(filling)
        return super().__new__(cls, *objs, category="constructive", **kwargs)

    @classmethod
    def specify_desc_ids(cls):
        cls.desc_ids = {
            "filling": c4d.DescID(c4d.DescLevel(c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS, c4d.DTYPE_REAL, 0))
        }

    @classmethod
    def set_values(cls, filling):
        cls.values = [1 - filling]

    @classmethod
    def specify_xpression(cls):
            cls.parameter_name = "Transparency"
            cls.interpolate = True


class Pulse(Fill):

    def __new__(cls, *objs, n=1, filling_lower=0, filling_upper=1, **kwargs):
        cls.set_values(n, filling_lower, filling_upper)
        return super(Fill, cls).__new__(cls, *objs, category="constructive", **kwargs)

    @classmethod
    def set_values(cls, n, filling_lower, filling_upper):
        cls.values = [n, filling_lower, filling_upper]

    @classmethod
    def specify_xpression(cls):
            cls.parameter_name = "Transparency"
            cls.udatas = [(UCount, "n"), (UStrength, "filling_lower"), (UStrength, "filling_upper")]
            cls.formula = "filling_lower + sin(n*Pi*t) * sin(n*Pi*t) * (filling_upper - filling_lower)"
