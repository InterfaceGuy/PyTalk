from abc import ABC, abstractmethod
from pydeation.animation.animation import StateAnimation, VectorAnimation, CompletionAnimation, AnimationGroup
from pydeation.xpresso.userdata import UParameter
from pydeation.xpresso.xpressions import XAnimation, XAnimator, XComposition
from iteration_utilities import deepflatten  # used to flatten groups
import c4d


class ProtoAnimator(ABC):
    """an animator mainly stores the information of which parameters will be animated and performs logic on the input values.
    it outputs only the necessary animations as an animation group and rescales them by the relative run time"""

    def __new__(cls, *objs, rel_start=0, rel_stop=1, relative=False, multiplicative=False, unpack_groups=True, animation_type="xvector", category=None, composition_mode=False):
        cls.document = c4d.documents.GetActiveDocument()
        cls.animation_type = animation_type
        # changes return values so it works with xcompositions
        cls.composition_mode = composition_mode
        cls.objs = cls.flatten_input(*objs, unpack_groups=unpack_groups)
        cls.specify_desc_ids()
        cls.specify_value_type()  # specify value type for vector animations
        cls.create_xpression()
        if cls.composition_mode:
            return cls.xanimators
        if cls.animation_type:
            cls.build_animation_group(
                relative=relative, multiplicative=multiplicative)
            animation_group_rescaled = cls.rescale_animation_group(
                rel_start, rel_stop)
            # add category for visibility handling
            animation_group_rescaled.category = category
            return animation_group_rescaled

    @abstractmethod
    def insert_helper_objects(cls):
        """inserts helper objects into the hierarchy if needed"""
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
    def specify_value_type(cls):
        """specifies the value type for vector animations"""
        cls.value_type = float  # float as default

    @classmethod
    def create_xpression(cls):
        """creates the xpresso setup for the animation if needed"""
        if cls.animation_type == "xvector":
            cls.completion_sliders = {}
            cls.animation_parameters = {}
            if cls.composition_mode:
                cls.xanimators = {}
            # set default specifications for xpression
            cls.udatas = []
            cls.formula = None
            cls.interpolate = False
            cls.reverse_parameter_range = False
            # set ideosynchratic specifications
            cls.specify_xpression()
            for obj in cls.objs:
                # check if object already has animator
                if cls.__name__ in obj.xpressions:
                    xanimator = obj.xpressions[cls.__name__]
                else:
                    link_target = cls.specify_target(obj)  # get link target
                    print(cls.parameter_name, link_target)
                    # only one descId in dict anyway, might be different for other animators
                    target_parameter_desc_id = list(cls.desc_ids.values())[0]
                    # check if object already has accessed given parameter
                    if str(target_parameter_desc_id) in obj.accessed_parameters:
                        parameter = obj.accessed_parameters[str(
                            target_parameter_desc_id)]
                    else:
                        parameter = UParameter(
                            obj, target_parameter_desc_id, link_target=link_target, name=cls.parameter_name)
                        # remember parameter
                        obj.accessed_parameters[str(
                            target_parameter_desc_id)] = parameter
                    xanimator = XAnimator(
                        obj, interpolate=cls.interpolate, formula=cls.formula, params=cls.udatas, name=cls.__name__)
                    # remember xanimator
                    obj.xpressions[cls.__name__] = xanimator
                    xanimation = XAnimation(
                        xanimator, target=obj, parameter=parameter, reverse_parameter_range=cls.reverse_parameter_range)
                if cls.composition_mode:
                    cls.xanimators[obj] = xanimator
                # save completion slider by obj
                cls.completion_sliders[obj] = xanimator.completion_slider
                # save parameters for animation by obj
                cls.animation_parameters[obj] = xanimator.animation_parameters

    @classmethod
    def specify_xpression(cls):
        """specifies the details of the xpresso setup"""
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
        # seperately add completion animation for xanimators
        if cls.animation_type == "xvector":
            completion_animation = CompletionAnimation(
                obj, cls.completion_sliders[obj].desc_id, value_ini=0, value_fin=1)
            animations.append(completion_animation)
        # create animation for each value
        for i, value in enumerate(cls.values):
            if value is not None:
                # specify the target to animate on
                target = cls.specify_target(obj)
                # create animation on target
                if cls.animation_type == "vector":
                    animation = VectorAnimation(
                        target, list(cls.desc_ids.values())[i], value_fin=value, relative=relative, multiplicative=multiplicative, value_type=cls.animation_parameters[obj][i].value_type)
                elif cls.animation_type == "xvector":
                    # check if list is not empty
                    if cls.animation_parameters[obj]:
                        animation = VectorAnimation(
                            obj, cls.animation_parameters[obj][i].desc_id, value_ini=value, value_fin=value, value_type=cls.animation_parameters[obj][i].value_type)
                    else:
                        continue
                elif cls.animation_type == "state":
                    animation = StateAnimation(
                        target, list(cls.desc_ids.values())[i], value=value)
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

    @classmethod
    def make_editable(cls, parametric_object):
        """makes a parametric object editable"""
        cls.document = c4d.documents.GetActiveDocument()
        bc = c4d.BaseContainer()
        editable_object = c4d.utils.SendModelingCommand(
            command=c4d.MCOMMAND_MAKEEDITABLE,
            list=[parametric_object],
            mode=c4d.MODELINGCOMMANDMODE_ALL,
            bc=bc,
            doc=cls.document)[0]

        cls.document.InsertObject(editable_object)
        c4d.EventAdd()
        return editable_object


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


class ComposedXAnimator(ProtoAnimator):
    """this class serves as a blueprint for XCompositions
        - values and xanimators must have the same order
        - the composition level specifies which xtag in the composition hierarchy the xpression is assigned to"""

    def __new__(cls, rel_start=0, rel_stop=1, category=None, composition_mode=False, composition_level=1):
        cls.composition_mode = composition_mode
        cls.composition_level = composition_level
        cls.create_xpression()
        if cls.composition_mode:
            return cls.xcomposers
        cls.build_animation_group()
        animation_group_rescaled = cls.rescale_animation_group(
            rel_start, rel_stop)
        # add category for visibility handling
        animation_group_rescaled.category = category
        return animation_group_rescaled

    @abstractmethod
    def set_values(cls):
        """sets values given by input and optionally performs logic on them"""
        pass

    @classmethod
    def create_xpression(cls):
        """creates the xpresso setup for the animation if needed"""
        cls.completion_sliders = {}
        cls.animation_parameters = {}
        if cls.composition_mode:
            cls.xcomposers = {}
        # set ideosynchratic specifications
        for obj in cls.objs:
            # check if object already has xcomposition
            if cls.__name__ in obj.xpressions:
                xcomposition = obj.xpressions[cls.__name__]
            else:
                xcomposition = XComposition(*cls.xanimator_tuples[obj], target=obj, name=cls.__name__,
                                            composition_mode=cls.composition_mode, composition_level=cls.composition_level)
                # remember xcomposition
                obj.xpressions[cls.__name__] = xcomposition
            # save descId of completion slider
            cls.completion_sliders[obj] = xcomposition.completion_slider
            # save descIds of udata elements
            cls.animation_parameters[obj] = []
            if cls.composition_mode:
                xcomposer = xcomposition.xcomposer
                # remember xcomposers
                cls.xcomposers[obj] = xcomposer
                # get ordered list of animation parameters of composed animators
                cls.animation_parameters[obj] = xcomposer.animation_parameters
            else:
                for xanimator in xcomposition.xanimators:
                    cls.animation_parameters[obj] += xanimator.animation_parameters

    @classmethod
    def build_animation_group_per_object(cls, obj):
        """intelligently builds animation group from only necessary animations given by value inputs for single object"""
        animations = []
        # seperately add completion animation for xcomposition
        completion_animation = CompletionAnimation(
            obj, cls.completion_sliders[obj].desc_id, value_ini=0, value_fin=1)
        animations.append(completion_animation)
        # create animation for each value
        for i, value in enumerate(cls.values):
            if value is not None:
                value_animation = VectorAnimation(
                    obj, cls.animation_parameters[obj][i].desc_id, value_ini=value, value_fin=value, value_type=cls.animation_parameters[obj][i].value_type)
                animations.append(value_animation)
        return AnimationGroup(*animations)

    @classmethod
    def build_animation_group(cls, relative=False, multiplicative=False):
        """loops over all objects and builds animation groups"""
        animation_groups = []
        for obj in cls.objs:
            animation_group = cls.build_animation_group_per_object(obj)
            animation_groups.append(animation_group)
        cls.animation_group = AnimationGroup(*animation_groups)

    @classmethod
    def compose_xanimators(cls, *xanimator_tuples):
        """reformats the xanimator tuples into readable format for xcomposition"""
        cls.xanimator_tuples = {}
        xanimators = [xanimator_tuple[0]
                      for xanimator_tuple in xanimator_tuples]
        input_ranges = [xanimator_tuple[1]
                        for xanimator_tuple in xanimator_tuples]
        for obj in cls.objs:
            cls.xanimator_tuples[obj] = []
            for xanimator, input_range in zip(xanimators, input_ranges):
                cls.xanimator_tuples[obj].append((xanimator[obj], input_range))
