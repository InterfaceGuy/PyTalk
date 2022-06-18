from pydeation.objects.abstract_objects import LineObject
from pydeation.objects.helper_objects import Group, MoSpline, SplineEffector, LinearField, SphericalField
from pydeation.animation.abstract_animators import SketchAnimator
from pydeation.xpresso.userdata import UParameter
from pydeation.xpresso.xpressions import XAnimation, XAnimator
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

    @classmethod
    def create_xpression(cls):
        for obj in cls.objs:
            for desc_id in cls.desc_ids.values():
                parameter = UParameter(
                    obj, desc_id, link_target=obj.sketch_material, name="SketchCompletion")
                xanimator = XAnimator(obj, interpolate=True, name="Draw")
                xanimation = XAnimation(
                    xanimator, target=obj, parameter=parameter)


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


class Morph(SketchAnimator):

    def __new__(cls, spline_ini: LineObject, spline_fin: LineObject, mode="linear", **kwargs):
        # calculate linear field offset
        cls.mode = mode
        cls.bounding_box = spline_ini.obj.GetRad()
        cls.bounding_box_center = spline_ini.obj.GetMp() + spline_ini.obj.GetAbsPos()
        cls.insert_helper_objects(spline_ini, spline_fin)
        cls.set_values()
        animations = super().__new__(cls, spline_ini, category="neutral",
                                     animation_type="xvector", **kwargs)
        return animations

    @classmethod
    def insert_helper_objects(cls, spline_ini, spline_fin):
        # get segment count of spline_fin spline
        target_clone = spline_fin.obj.GetClone()
        target_clone_editable = cls.make_editable(target_clone)
        segment_count = target_clone_editable.GetSegmentCount()
        # get helper objects
        if cls.mode == "linear":
            field = LinearField(direction="x-")
        elif cls.mode == "constant":
            x, y, z = cls.bounding_box_center.x, cls.bounding_box_center.y, cls.bounding_box_center.z
            field = SphericalField(radius=cls.bounding_box.GetLength() * 1.1,
                                   x=x, y=y, z=z)

        spline_effectors = Group(*[SplineEffector(spline=spline_fin, fields=[field], segment_index=i)
                                   for i in range(segment_count)], name="SplineEffectors")
        mosplines = Group(*[MoSpline(source_spline=spline_ini)
                            for i in range(segment_count)], name="MoSplines")
        # add spline effectors to mosplines
        for mospline, spline_effector in zip(mosplines, spline_effectors):
            mospline.add_effectors(spline_effector)
        morph_setup = Group(mosplines, spline_effectors,
                            field, name=f"Morph:{spline_ini.name}->{spline_fin.name}")
        # add to helper_objects
        spline_ini.helper_objects["morph_mosplines"] = mosplines
        spline_ini.helper_objects["morph_field"] = field
        spline_ini.helper_objects["morph_spline_effectors"] = spline_effectors

    @classmethod
    def specify_target(cls, obj):
        target = obj.helper_objects["morph_field"]
        return target

    @classmethod
    def set_values(cls):
        cls.values = [1]

    @classmethod
    def specify_desc_ids(cls):
        if cls.mode == "linear":
            cls.desc_ids = {
                "pos_x": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_POSITION, c4d.DTYPE_VECTOR, 0),
                                    c4d.DescLevel(c4d.VECTOR_X, c4d.DTYPE_REAL, 0))
            }
        elif cls.mode == "constant":
            cls.desc_ids = {
                "field_strength": c4d.DescID(c4d.DescLevel(c4d.FIELD_STRENGTH, c4d.DTYPE_REAL, 0))
            }

    @classmethod
    def specify_xpression(cls):
        cls.parameter_name = "MorphCompletion"
        if cls.mode == "linear":
            cls.formula = f"t*2*{cls.bounding_box.x * 1.1}-{cls.bounding_box.x * 1.1}"
