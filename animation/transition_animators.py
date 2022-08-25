from pydeation.objects.abstract_objects import LineObject
from pydeation.objects.custom_objects import Group, Morpher
from pydeation.animation.abstract_animators import ProtoAnimator, abstractmethod
from pydeation.animation.object_animators import Hide, Show
from pydeation.animation.animation import AnimationGroup
from pydeation.utils import match_indices
import c4d


class TransitionAnimator(ProtoAnimator):
    """abstract animator for handling transition animations"""
    def __new__(cls, obj_ini, obj_fin, transition_obj, **kwargs):
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

    def __new__(cls, spline_ini: LineObject, spline_fin: LineObject, linear_field_length=50, **kwargs):
        cls.spline_ini = spline_ini
        cls.spline_fin = spline_fin
        cls.linear_field_length = linear_field_length
        cls.insert_helper_objects()
        cls.set_values()
        morph_animations = super().__new__(cls, spline_ini, spline_fin, cls.morpher, category="neutral",
                                           animation_type="xvector", **kwargs)
        return morph_animations

    @classmethod
    def insert_helper_objects(cls):
        cls.morpher = Morpher(cls.spline_ini, cls.spline_fin,
                              linear_field_length=cls.linear_field_length)

    @classmethod
    def specify_target(cls, obj):
        target = obj
        return target

    @classmethod
    def set_values(cls):
        cls.values = [1]

    @classmethod
    def specify_desc_ids(cls):
        cls.desc_ids = {
            "morph_completion": cls.morpher.morph_completion_parameter.desc_id
        }

    @classmethod
    def create_xpression(cls):
        pass
