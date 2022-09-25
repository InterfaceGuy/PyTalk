from abc import ABC, abstractmethod
from pydeation.animation.animation import BoolAnimation, ScalarAnimation, CompletionAnimation, AnimationGroup
from pydeation.xpresso.userdata import UParameter
from pydeation.xpresso.xpressions import XAnimation, XAnimator, XComposition
from iteration_utilities import deepflatten  # used to flatten groups
import c4d


class ProtoAnimator(ABC):
    """an animator is a very thin wrapper that accesses the respective animation methods of its input objects.
    it outputs only the necessary animations as an animation group and rescales them by the relative run time"""

    def __init__(self, *objs, rel_start=0, rel_stop=1, relative=False, multiplicative=False, unpack_groups=True, animation_type="xvector", category=None, **kwargs):
        self.document = c4d.documents.GetActiveDocument()
        self.objs = objs
        self.rel_start = rel_start
        self.rel_stop = rel_stop
        self.relative = relative
        self.multiplicative = multiplicative
        self.unpack_groups = unpack_groups
        self.animation_type = animation_type
        self.category = category
        self.kwargs = kwargs

        self.specify_animation_method()
        self.flatten_input()
        self.build_animation_group()
        self.rescale_animation_group()
        # add category for visibility handling
        self.animation_group.category = category
        self.animations = self.animation_group

    def specify_animation_method(self):
        """specifies the method used for the animation"""
        self.animation_method = self.__class__.__name__.lower()

    def insert_helper_objects(self):
        """inserts helper objects into the hierarchy if needed"""
        pass

    def flatten_input(self):
        """flattens the input to the specified depth:
            True: all levels
            False: zero levels
            int: n levels"""
        if type(self.unpack_groups) is int:
            depth = self.unpack_groups  # interpret as depth
            flattened_objs = list(deepflatten(self.objs, depth=depth))
            self.objs = flattened_objs
        elif type(self.unpack_groups) is bool:
            if self.unpack_groups:
                flattened_objs = list(deepflatten(self.objs))
                self.objs = flattened_objs

    def build_animation_group(self):
        """loops over all objects and builds animation groups"""
        animations = []
        for obj in self.objs:
            animation = getattr(obj, self.animation_method)(**self.kwargs)
            animations.append(animation)
        self.animation_group = AnimationGroup(*animations)

    def rescale_animation_group(self):
        """rescales the animations using relative start/stop"""
        animation_group_rescaled = AnimationGroup(
            (self.animation_group, (self.rel_start, self.rel_stop)))
        self.animation_group = animation_group_rescaled


class Create(ProtoAnimator):
    pass


class UnCreate(ProtoAnimator):
    pass


class Draw(ProtoAnimator):
    pass


class UnDraw(ProtoAnimator):
    pass


class Fill(ProtoAnimator):
    pass


class UnFill(ProtoAnimator):
    pass


class Move(ProtoAnimator):
    pass


class Scale(ProtoAnimator):
    pass


class Rotate(ProtoAnimator):
    pass


class ComposedAnimator(ProtoAnimator):
    """this class serves as a blueprint for Animators that are composed from simpler ones"""

    def __init__(self, rel_start=0, rel_stop=1, category=None):
        animation_group_rescaled = self.rescale_animation_group(
            rel_start, rel_stop)
        # add category for visibility handling
        animation_group_rescaled.category = category
        self.animations = animation_group_rescaled

    @abstractmethod
    def digest_values(self):
        """performs logic on the relevant input values"""
        pass

    def compose_animators(self, *animators):
        """composes the animators into one animation group"""
        self.animation_group = AnimationGroup(*animators)


class ComposedXAnimator(ProtoAnimator):
    """this class serves as a blueprint for XCompositions
        - values and xanimators must have the same order
        - the composition level specifies which xtag in the composition hierarchy the xpression is assigned to"""

    def __init__(self, rel_start=0, rel_stop=1, category=None, composition_mode=False, composition_level=1):
        self.composition_mode = composition_mode
        self.composition_level = composition_level
        self.create_xpression()
        if self.composition_mode:
            return self.xcomposers
        self.build_animation_group()
        animation_group_rescaled = self.rescale_animation_group(
            rel_start, rel_stop)
        # add category for visibility handling
        animation_group_rescaled.category = category
        return animation_group_rescaled

    @abstractmethod
    def set_values(self):
        """sets values given by input and optionally performs logic on them"""
        pass

    def create_xpression(self):
        """creates the xpresso setup for the animation if needed"""
        self.completion_sliders = {}
        self.animation_parameters = {}
        if self.composition_mode:
            self.xcomposers = {}
        # set ideosynchratic specifications
        for obj in self.objs:
            # check if object already has xcomposition
            if self.__name__ in obj.xpressions:
                xcomposition = obj.xpressions[self.__name__]
            else:
                xcomposition = XComposition(*self.xanimator_tuples[obj], target=obj, name=self.__name__,
                                            composition_mode=self.composition_mode, composition_level=self.composition_level)
                # remember xcomposition
                obj.xpressions[self.__name__] = xcomposition
            # save descId of completion slider
            self.completion_sliders[obj] = xcomposition.completion_slider
            # save descIds of udata elements
            self.animation_parameters[obj] = []
            if self.composition_mode:
                xcomposer = xcomposition.xcomposer
                # remember xcomposers
                self.xcomposers[obj] = xcomposer
                # get ordered list of animation parameters of composed animators
                self.animation_parameters[obj] = xcomposer.animation_parameters
            else:
                for xanimator in xcomposition.xanimators:
                    self.animation_parameters[obj] += xanimator.animation_parameters

    def build_animation_group_per_object(self, obj):
        """intelligently builds animation group from only necessary animations given by value inputs for single object"""
        animations = []
        # seperately add completion animation for xcomposition
        completion_animation = CompletionAnimation(
            obj, self.completion_sliders[obj].desc_id, value_ini=0, value_fin=1)
        animations.append(completion_animation)
        # create animation for each value
        for i, value in enumerate(self.values):
            if value is not None:
                value_animation = ScalarAnimation(
                    obj, self.animation_parameters[obj][i].desc_id, value_ini=value, value_fin=value, value_type=self.animation_parameters[obj][i].value_type)
                animations.append(value_animation)
        return AnimationGroup(*animations)

    def build_animation_group(self, relative=False, multiplicative=False):
        """loops over all objects and builds animation groups"""
        animation_groups = []
        for obj in self.objs:
            animation_group = self.build_animation_group_per_object(obj)
            animation_groups.append(animation_group)
        self.animation_group = AnimationGroup(*animation_groups)

    def compose_xanimators(self, *xanimator_tuples):
        """reformats the xanimator tuples into readable format for xcomposition"""
        self.xanimator_tuples = {}
        xanimators = [xanimator_tuple[0]
                      for xanimator_tuple in xanimator_tuples]
        input_ranges = [xanimator_tuple[1]
                        for xanimator_tuple in xanimator_tuples]
        for obj in self.objs:
            self.xanimator_tuples[obj] = []
            for xanimator, input_range in zip(xanimators, input_ranges):
                self.xanimator_tuples[obj].append(
                    (xanimator[obj], input_range))
