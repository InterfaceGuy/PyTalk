from pydeation.animation.abstract_animators import ComposedAnimator
from pydeation.animation.object_animators import *
from pydeation.animation.sketch_animators import *
from pydeation.animation.fill_animators import *

class Transform(ComposedAnimator):

    def __new__(cls, *objs, x=None, y=None, z=None, h=None, p=None, b=None, scale=None, scale_x=None, scale_y=None, scale_z=None, relative=True, transform_children=False, **kwargs):
        # compute values
        scale_x, scale_y, scale_z = cls.digest_values(
            scale, scale_x, scale_y, scale_z)
        # compose animators
        cls.compose_animators(Move(*objs, x=x, y=y, z=z, relative=relative, unpack_groups=transform_children), Rotate(
            *objs, h=h, p=p, b=b, relative=relative, unpack_groups=transform_children), Scale(*objs, x=scale_x, y=scale_y, z=scale_z, relative=relative, unpack_groups=transform_children))
        return super().__new__(cls, **kwargs)

    @classmethod
    def digest_values(cls, scale, scale_x, scale_y, scale_z):
        """performs logic on the relevant input values"""
        if scale is not None:
            scale_x = scale_y = scale_z = scale
        return scale_x, scale_y, scale_z

class DrawThenFill(ComposedAnimator):

    def __new__(cls, *objs, drawing=1, filling=1, **kwargs):
        # compose animators
        cls.compose_animators(
            Draw(*objs, drawing=drawing),
            Fill(*objs, filling=filling))
        return super().__new__(cls, category="constructive", **kwargs)
