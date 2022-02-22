from pydeation.animation.abstract_animators import FillAnimator
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
