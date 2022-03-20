from abc import ABC, abstractmethod
from pydeation.animation.animation import StateAnimation, VectorAnimation, AnimationGroup
from iteration_utilities import deepflatten  # used to flatten groups


class ProtoAnimator(ABC):
    """an animator mainly stores the information of which parameters will be animated and performs logic on the input values.
    it outputs only the necessary animations as an animation group and rescales them by the relative run time"""

    def __new__(cls, *objs, rel_start=0, rel_stop=1, relative=False, multiplicative=False, unpack_groups=True, animation_type="vector", category=None):
        cls.animation_type = animation_type
        cls.objs = cls.flatten_input(*objs, unpack_groups=unpack_groups)
        #cls.create_xpression()
        cls.specify_desc_ids()
        cls.set_initial_values()
        cls.build_animation_group(
            relative=relative, multiplicative=multiplicative)
        animation_group_rescaled = cls.rescale_animation_group(
            rel_start, rel_stop)
        # add category for visibility handling
        animation_group_rescaled.category = category
        return animation_group_rescaled

    @abstractmethod
    def create_xpression(cls):
        """creates the xpresso setup for the animation if needed"""
        pass

    @abstractmethod
    def specify_desc_ids(cls):
        """specifies the description ids addressed by the animator"""
        pass

    @abstractmethod
    def set_values(cls):
        """sets values given by input and optionally performs logic on them"""
        pass

    @abstractmethod
    def specify_target(cls):
        """specifies the target to animate on"""
        pass

    @classmethod
    def set_initial_values(cls):
        pass

    @classmethod
    def flatten_input(cls, *objs, unpack_groups=True):
        """flattens the input to the specified depth:
            True: all levels
            False: zero levels
            int: n levels"""

        if type(unpack_groups) is int:
            depth = unpack_groups  # interpret as depth
            flattened_input = list(deepflatten(objs, depth=depth))
            return flattened_input
        elif type(unpack_groups) is bool:
            if unpack_groups:
                flattened_input = list(deepflatten(objs))
                return flattened_input
            else:
                return objs

    @classmethod
    def build_animation_group_per_object(cls, obj, relative=False, multiplicative=False):
        """intelligently builds animation group from only necessary animations given by value inputs for single object"""
        animations = []
        for i, value in enumerate(cls.values):
            if value is not None:
                # specify the target to animate on
                target = cls.specify_target(obj)
                # create animation on target
                if cls.animation_type == "vector":
                    animation = VectorAnimation(
                        target, list(cls.desc_ids.values())[i], value, relative=relative, multiplicative=multiplicative)
                elif cls.animation_type == "state":
                    animation = StateAnimation(
                        target, list(cls.desc_ids.values())[i], value)
                animations.append(animation)
        return AnimationGroup(*animations)

    @classmethod
    def build_animation_group(cls, relative=False, multiplicative=False):
        """loops over all objects and builds animation groups"""
        animation_groups = []
        for obj in cls.objs:
            animation_group = cls.build_animation_group_per_object(
                obj, relative=relative, multiplicative=multiplicative)
            animation_groups.append(animation_group)
        cls.animation_group = AnimationGroup(*animation_groups)

    @classmethod
    def rescale_animation_group(cls, rel_start, rel_stop):
        """rescales the animations using relative start/stop"""
        return AnimationGroup((cls.animation_group, (rel_start, rel_stop)))


class ObjectAnimator(ProtoAnimator):
    """abstract animator for handling sketch animations"""
    def __new__(cls, *objs, **kwargs):
        return super().__new__(cls, *objs, **kwargs)

    @abstractmethod
    def specify_desc_ids(cls):
        """specifies the description ids addressed by the animator"""
        pass

    @abstractmethod
    def set_values(cls):
        """sets values given by input and optionally performs logic on them"""
        pass

    @classmethod
    def specify_target(cls, obj):
        """specifies the target to animate on"""
        target = obj
        return target


class SketchAnimator(ProtoAnimator):
    """abstract animator for handling sketch animations"""
    def __new__(cls, *objs, **kwargs):
        return super().__new__(cls, *objs, **kwargs)

    @abstractmethod
    def specify_desc_ids(cls):
        """specifies the description ids addressed by the animator"""
        pass

    @abstractmethod
    def set_values(cls):
        """sets values given by input and optionally performs logic on them"""
        pass

    @classmethod
    def specify_target(cls, obj):
        """specifies the target to animate on"""
        target = obj.sketch_material
        return target


class FillAnimator(ProtoAnimator):
    """abstract animator for handling sketch animations"""
    def __new__(cls, *objs, **kwargs):
        return super().__new__(cls, *objs, **kwargs)

    @abstractmethod
    def specify_desc_ids(cls):
        """specifies the description ids addressed by the animator"""
        pass

    @abstractmethod
    def set_values(cls):
        """sets values given by input and optionally performs logic on them"""
        pass

    @classmethod
    def specify_target(cls, obj):
        """specifies the target to animate on"""
        target = obj.fill_material
        return target


class ComposedAnimator(ProtoAnimator):
    """this class serves as a blueprint for Animators that are composed from simpler ones"""

    def __new__(cls, rel_start=0, rel_stop=1, category=None):
        animation_group_rescaled = cls.rescale_animation_group(
            rel_start, rel_stop)
        # add category for visibility handling
        animation_group_rescaled.category = category
        return animation_group_rescaled

    @abstractmethod
    def digest_values(cls):
        """performs logic on the relevant input values"""
        pass

    @classmethod
    def compose_animators(cls, *animators):
        """composes the animators into one animation group"""
        cls.animation_group = AnimationGroup(*animators)
