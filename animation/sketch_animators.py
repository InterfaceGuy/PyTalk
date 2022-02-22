from pydeation.animation.abstract_animators import SketchAnimator
import c4d

class Draw(SketchAnimator):

    def __new__(cls, *objs, drawing=1, **kwargs):
        cls.set_values(drawing)
        return super().__new__(cls, *objs, category="constructive", **kwargs)

    @classmethod
    def specify_desc_ids(cls):
        cls.desc_ids = {
            "drawing": c4d.DescID(c4d.DescLevel(c4d.OUTLINEMAT_ANIMATE_STROKE_SPEED_COMPLETE, c4d.DTYPE_REAL, 0))
        }

    @classmethod
    def set_values(cls, drawing):
        cls.values = [drawing]

    @classmethod
    def set_initial_values(cls):
        for obj in cls.objs:
            obj.sketch_material.obj[c4d.OUTLINEMAT_ANIMATE_AUTODRAW] = True
            obj.sketch_material.obj[c4d.OUTLINEMAT_ANIMATE_STROKE_SPEED_TYPE] = 2
            obj.sketch_material.obj[c4d.OUTLINEMAT_ANIMATE_STROKE_SPEED_COMPLETE] = 0


class UnDraw(SketchAnimator):

    def __new__(cls, *objs, drawing=0, **kwargs):
        cls.set_values(drawing)
        return super().__new__(cls, *objs, category="destructive", **kwargs)

    @classmethod
    def specify_desc_ids(cls):
        cls.desc_ids = {
            "drawing": c4d.DescID(c4d.DescLevel(c4d.OUTLINEMAT_ANIMATE_STROKE_SPEED_COMPLETE, c4d.DTYPE_REAL, 0))
        }

    @classmethod
    def set_values(cls, drawing):
        cls.values = [drawing]
