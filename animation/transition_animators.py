from pydeation.objects.abstract_objects import LineObject
from pydeation.objects.helper_objects import Group, MoSpline, SplineEffector, LinearField, SphericalField
from pydeation.animation.abstract_animators import ProtoAnimator, abstractmethod
from pydeation.animation.object_animators import Hide, Show
from pydeation.animation.animation import AnimationGroup
from pydeation.utils import match_indices
import c4d


class TransitionAnimator(ProtoAnimator):
    """abstract animator for handling transition animations"""
    def __new__(cls, obj_ini, obj_fin, transition_obj, **kwargs):
        print(1, transition_obj)
        transition_animation = super().__new__(cls, obj_ini, **kwargs)
        hide_obj_ini_animation = (Hide(obj_ini), (0, 1))
        show_obj_fin_animation = (Show(obj_fin), (1, 1))
        show_transition_obj_animation = (
            Show(transition_obj, unpack_groups=False), (0, 1))
        hide_transition_obj_animation = (
            Hide(transition_obj, unpack_groups=False), (1, 1))
        return AnimationGroup(transition_animation, hide_obj_ini_animation, show_obj_fin_animation, show_transition_obj_animation, hide_transition_obj_animation)

    @abstractmethod
    def specify_desc_ids(cls):
        """specifies the description ids addressed by the animator"""
        pass

    @abstractmethod
    def set_values(cls):
        """sets values given by input and optionally performs logic on them"""
        pass

    @abstractmethod
    def specify_target(cls, obj):
        """specifies the target to animate on"""
        pass


class Morph(TransitionAnimator):

    def __new__(cls, spline_ini: LineObject, spline_fin: LineObject, match_segments=True, mode="linear", linear_field_length=50, **kwargs):
        # calculate linear field offset
        cls.mode = mode
        cls.match_segments = match_segments
        cls.linear_field_length = linear_field_length
        cls.bounding_box = spline_ini.obj.GetRad()
        cls.bounding_box_center = spline_ini.obj.GetMp() + spline_ini.obj.GetAbsPos()
        cls.insert_helper_objects(spline_ini, spline_fin)
        cls.set_values()
        morph_animations = super().__new__(cls, spline_ini, spline_fin, cls.morph_setup, category="neutral",
                                           animation_type="xvector", **kwargs)
        return morph_animations

    @classmethod
    def insert_helper_objects(cls, spline_ini, spline_fin):
        # get segment count of splines
        spline_ini_clone = spline_ini.obj.GetClone()
        spline_ini_clone_editable = cls.make_editable(spline_ini_clone)
        spline_fin_clone = spline_fin.obj.GetClone()
        spline_fin_clone_editable = cls.make_editable(spline_fin_clone)
        segment_count_ini = spline_ini_clone_editable.GetSegmentCount() + \
            1  # shift to natural counting
        segment_count_fin = spline_fin_clone_editable.GetSegmentCount() + \
            1  # shift to natural counting
        if cls.mode == "match_segments":
            segment_count = max(segment_count_ini, segment_count_fin)
        else:
            segment_count = segment_count_fin
        # get helper objects
        if cls.mode == "linear":
            field = LinearField(direction="x-", length=cls.linear_field_length)
        elif cls.mode == "constant":
            x, y, z = cls.bounding_box_center.x, cls.bounding_box_center.y, cls.bounding_box_center.z
            field = SphericalField(radius=cls.bounding_box.GetLength() * 1.1,
                                   x=x, y=y, z=z)
        if cls.match_segments:
            spline_effectors_ini = Group(*[SplineEffector(spline=spline_ini, segment_index=i, name=f"SplineEffector{i}")
                                           for i in range(segment_count_ini)], name="SplineEffectorsInitial")
            spline_effectors_fin = Group(*[SplineEffector(spline=spline_fin, fields=[field], segment_index=i, name=f"SplineEffector{i}")
                                           for i in range(segment_count_fin)], name="SplineEffectors")
        else:
            spline_effectors = Group(*[SplineEffector(spline=spline_fin, fields=[field], segment_index=i, name=f"SplineEffector{i}")
                                       for i in range(segment_count)], name="SplineEffectors")
        mosplines = Group(*[MoSpline(source_spline=spline_ini, name=f"MoSpline{i}")
                            for i in range(segment_count)], name="MoSplines")
        # add spline effectors to mosplines
        if cls.match_segments:
            # we want to match the segments in the most natural way using modulu
            indices_ini, indices_fin = match_indices(
                segment_count_ini, segment_count_fin)
            print(segment_count_ini, segment_count_fin)
            print(spline_effectors_ini, spline_effectors_fin)
            for i, j, mospline in zip(indices_ini, indices_fin, mosplines):
                print(i, j)
                mospline.add_effectors(
                    spline_effectors_ini[i], spline_effectors_fin[j])
            cls.morph_setup = Group(mosplines, spline_effectors_fin, spline_effectors_ini,
                                    field, name=f"Morph:{spline_ini.name}->{spline_fin.name}")
        else:
            for mospline, spline_effector in zip(mosplines, spline_effectors):
                mospline.add_effectors(spline_effector)
            cls.morph_setup = Group(mosplines, spline_effectors,
                                    field, name=f"Morph:{spline_ini.name}->{spline_fin.name}")
        # add to helper_objects
        spline_ini.helper_objects["morph_mosplines"] = mosplines
        spline_ini.helper_objects["morph_field"] = field
        if cls.match_segments:
            spline_ini.helper_objects["morph_spline_effectors_ini"] = spline_effectors_ini
            spline_ini.helper_objects["morph_spline_effectors_fin"] = spline_effectors_fin
        else:
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
            cls.formula = f"t*2*{cls.bounding_box.x * 1.3 + cls.linear_field_length}-{cls.bounding_box.x * 1.3 + cls.linear_field_length}"
