from pydeation.animation.abstract_animators import FillAnimator
from pydeation.xpresso.userdata import UParameter
from pydeation.xpresso.xpressions import XAnimation, XAnimator
import c4d

class Fill(FillAnimator):

    def __new__(cls, *objs, filling=1, **kwargs):
        cls.set_values(filling)
        return super().__new__(cls, *objs, category="constructive", animation_type="xvector", **kwargs)

    @classmethod
    def specify_desc_ids(cls):
        cls.desc_ids = {
            "filling": c4d.DescID(c4d.DescLevel(c4d.MATERIAL_TRANSPARENCY_BRIGHTNESS, c4d.DTYPE_REAL, 0))
        }

    @classmethod
    def set_values(cls, filling):
        cls.values = [1 - filling]


    @classmethod
    def create_xpression(cls):
        cls.completion_sliders = []
        for obj in cls.objs:
            link_target = cls.specify_target(obj)  # get link target
            for i, desc_id in enumerate(cls.desc_ids.values()):
                parameter = UParameter(obj, desc_id, link_target=link_target, name="Transparency")
                xanimator = XAnimator(obj, interpolate=True, name="Fill")
                cls.completion_sliders.append(xanimator.completion_slider.desc_id)  # save descId of completion slider
                xanimation = XAnimation(xanimator, target=obj, parameter=parameter)
