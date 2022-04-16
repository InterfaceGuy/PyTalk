from abc import ABC, abstractmethod
from pydeation.constants import WHITE
import c4d


class KeyFrame:
    """a keyframe object is responsible for creating a keyframe in c4d for a single target for a single description id
    with a specific value and time"""

    def __init__(self, target, desc_id, value=None, time=None):
        self.document = c4d.documents.GetActiveDocument()  # get document
        self.target = target
        self.desc_id = desc_id
        self.time = self.check_time(time)
        self.track = self.get_track()
        self.curve = self.get_curve(self.track)
        self.key = self.set_key(self.time)
        self.value = self.set_value(value)

    def get_track(self):
        """finds or create the animation track for the given target"""
        track = self.target.obj.FindCTrack(self.desc_id)
        if track is None:
            track = c4d.CTrack(self.target.obj, self.desc_id)
            # insert ctrack into objects timeline
            self.target.obj.InsertTrackSorted(track)
        return track

    def get_curve(self, track):
        """creates animation curve for the animation track"""
        curve = track.GetCurve()
        return curve

    def set_key(self, time):
        """creates a key on the curve at a given time"""
        key = self.curve.AddKey(time)["key"]
        return key

    def check_time(self, time):
        """returns document's current time if time is None"""
        if time is None:
            time = self.document.GetTime()
        return time

    def set_value(self, value):
        """sets the value of the key"""
        if type(value) in (bool, int, c4d.Vector):  # used for state changing keyframes like visibility
            self.key.SetGeData(self.curve, value)
        else:  # general case
            self.key.SetValue(self.curve, value)


class Animation(ABC):
    """an animation object is responsible for setting keyframes for a single description id for a single object"""

    def __init__(self, target, desc_id, value_type, name=None):
        self.document = c4d.documents.GetActiveDocument()  # get document
        self.abs_run_time = 1  # set default to 1 second
        self.target = target  # the target that is animated on
        self.desc_id = desc_id  # holds the description id of the animation
        # the param id is needed to receive the current value
        self.param_id = self.get_param_id()
        self.value_type = value_type  # enforces the correct data type for the value
        self.name = name  # sets the name of the animation for printing

    @abstractmethod
    def __repr__(self):
        """sets the string representation for printing"""
        pass

    @abstractmethod
    def execute(self):
        """sets the actual keyframes of the animation"""
        pass

    @abstractmethod
    def scale_relative_run_time(self, abs_run_time):
        """scales the relative run time by the absolute run time"""
        pass

    @abstractmethod
    def rescale_relative_run_time(self, super_rel_run_time):
        """rescales the current relative run time using the superordinate relative run time"""
        pass

    def get_param_id(self):
        """returns the parameter id from the description id to use for setting parameter values of objects"""
        if self.desc_id.GetDepth() == 1:
            param_id = (self.desc_id[0].id)
        elif self.desc_id.GetDepth() == 2:
            param_id = (self.desc_id[0].id, self.desc_id[1].id)
        elif self.desc_id.GetDepth() == 3:
            param_id = (self.desc_id[0].id,
                        self.desc_id[1].id, self.desc_id[2].id)
        return param_id

    def get_current_value(self):
        """returns the value of the objects parameter"""
        param_id = self.get_param_id()
        current_value = self.target.obj[param_id]
        return current_value

    def global_time(self, time: c4d.BaseTime):
        """adds the current document time to the scaled run time"""
        current_time = self.document.GetTime()
        global_time = current_time + time
        return global_time


class VectorAnimation(Animation):
    """a vector animation object is responsible for setting an initial and final keyframe for a single description id for a single object
    the keyframes are spaced internally only on a relative scale and have to be scaled by the absolute run time provided by the Scene.play() function"""

    def __init__(self, target, desc_id, value_fin=None, value_ini=None, value_type=float, rel_start=0, rel_stop=1, relative=False, multiplicative=False, **kwargs):
        super().__init__(target, desc_id, value_type, **kwargs)
        # used for multiplicative relative animations like e.g. scale
        self.multiplicative = multiplicative
        self.relative = relative  # specifies whether animation is relative or absolute
        self.rel_start = rel_start  # the relative start time depending on absolute run time
        self.rel_stop = rel_stop  # the relative stop time depending on absolute run time
        self.set_value_ini(value_ini)
        self.set_value_fin(value_fin)

    def __repr__(self):
        """sets the string representation for printing"""
        if self.name is None:
            return f"VectorAnimation: {self.target}, {self.value_ini}, {self.value_fin}"
        else:
            return f"VectorAnimation: {self.name}, {self.target}, {self.value_ini}, {self.value_fin}"

    def __iadd__(self, other):
        """adds a given value to both initial and final value of the animation simultaneously
        thus shifting the one dimensinal vector by some one dimensional vector"""
        # calculate new values
        value_ini = other.get_vector() + self.value_ini
        value_fin = other.get_vector() + self.value_fin
        # set new values
        self.set_value_ini(value_ini)
        self.set_value_fin(value_fin, ignore_relative=True)
        return self

    def execute(self):
        """sets the actual keyframes of the animation"""
        # translate relative to absolute run time
        self.scale_relative_run_time(self.abs_run_time)
        # calculate offset frame for initial keyframe
        offset = 1 / self.document.GetFps()
        # set keyframes
        self.key_ini = KeyFrame(
            self.target, self.desc_id, value=self.value_ini, time=self.global_time(self.abs_start))  # create initial keyframe
        self.key_fin = KeyFrame(
            self.target, self.desc_id, value=self.value_fin, time=self.global_time(self.abs_stop - offset))  # create final keyframe

    def scale_relative_run_time(self, abs_run_time):
        """scales the relative run time by the absolute run time"""
        self.abs_start = self.rel_start * abs_run_time
        self.abs_stop = self.rel_stop * abs_run_time

    def rescale_relative_run_time(self, super_rel_run_time):
        """rescales the current relative run time using the superordinate relative run time"""
        # get start and endpoint of superordinate relative run time
        super_rel_start_point = super_rel_run_time[0]
        super_rel_end_point = super_rel_run_time[1]
        # get length of superordinate relative run time
        super_rel_run_time_length = super_rel_end_point - super_rel_start_point
        # rescale run time
        rel_start_rescaled = super_rel_run_time_length * self.rel_start
        rel_stop_rescaled = super_rel_run_time_length * self.rel_stop
        # translate run time
        rel_start_rescaled_translated = rel_start_rescaled + super_rel_start_point
        rel_stop_rescaled_translated = rel_stop_rescaled + super_rel_start_point
        # write to animation
        self.rel_start = rel_start_rescaled_translated
        self.rel_stop = rel_stop_rescaled_translated

    def set_value_ini(self, value):
        """sets the initial value of the animation"""
        if value is None:
            value_ini = self.get_current_value()
        else:
            value_ini = value
        # make sure it's correct data_type
        self.value_ini = self.value_type(value_ini)

    def set_value_fin(self, value, ignore_relative=False):
        """sets the final value of the animation
        the ignore_relative parameter is used later in the Scene.link_animation_chains() method in case relative=True"""
        if self.relative and not ignore_relative:
            if self.multiplicative:
                value *= self.get_current_value()
            else:
                value += self.get_current_value()
        # make sure it's correct data_type
        self.value_fin = self.value_type(value)

    def get_vector(self):
        """returns the vector i.e. the the difference between final and initial value"""
        vector = self.value_fin - self.value_ini
        return vector


class CompletionAnimation(VectorAnimation):
    """subclass used for differentiating completion animations when linking animation chains"""

    def __init__(self, target, desc_id, **kwargs):
        super().__init__(target, desc_id, **kwargs)

    def __repr__(self):
        """sets the string representation for printing"""
        if self.name is None:
            return f"CompletionAnimation: {self.target}, {self.value_ini}, {self.value_fin}"
        else:
            return f"CompletionAnimation: {self.name}, {self.target}, {self.value_ini}, {self.value_fin}"


class StateAnimation(Animation):
    """a state animation object is responsible for setting a single keyframe for a single (state like e.g. visibility) description id for a single object
    the keyframe is placed internally only on a relative scale and has to be scaled by the absolute run time provided by the Scene.play() function"""

    def __init__(self, target, desc_id, value=None, value_type=bool, rel_start=0, **kwargs):
        super().__init__(target, desc_id, value_type, **kwargs)
        self.rel_start = rel_start
        self.set_value(value)

    def __repr__(self):
        """sets the string representation for printing"""
        if self.name is None:
            return f"StateAnimation: {self.target}, {self.value}"
        else:
            return f"StateAnimation: {self.name}, {self.target}, {self.value}"

    def execute(self):
        """sets the actual keyframes of the animation"""
        self.scale_relative_run_time(
            self.abs_run_time)  # translates the relative to absolute run time
        self.key = KeyFrame(
            self.target, self.desc_id, value=self.value, time=self.global_time(self.abs_start))  # create initial keyframe

    def set_value(self, value):
        """sets the value of the animation"""
        if value is None:
            value = self.get_current_value()
        # make sure it's correct data_type
        self.value = self.value_type(value)

    def scale_relative_run_time(self, abs_run_time):
        """scales the relative run time by the absolute run time"""
        self.abs_start = self.rel_start * abs_run_time

    def rescale_relative_run_time(self, super_rel_run_time):
        """rescales the current relative run time using the superordinate relative run time
        for backwards compatibility we reuse the vector animation method with only slight alteration"""
        # get start and endpoint of superordinate relative run time
        super_rel_start_point = super_rel_run_time[0]
        super_rel_end_point = super_rel_run_time[1]
        # get length of superordinate relative run time
        super_rel_run_time_length = super_rel_end_point - super_rel_start_point
        # rescale run time
        rel_start_rescaled = super_rel_run_time_length * self.rel_start
        # translate run time
        rel_start_rescaled_translated = rel_start_rescaled + super_rel_start_point
        # write to animation
        self.rel_start = rel_start_rescaled_translated


class AnimationGroup:
    """an animation group holds a set of animations and can be used to recursively nest sets of animations and perform transformations on those"""

    def __init__(self, *animations, category=None):
        """animations here refer to single animations or animation groups both with and without a relative run time attached"""
        self.animations = self.digest_input(animations)
        self.category = category

    def __repr__(self):
        strings = "AnimationGroup: "
        for animation in self.animations:
            strings += str(animation) + "; "
        return strings

    def digest_input(self, animations):
        """applies all necessary transformations on the animations"""
        rescaled_animations = self.rescale_other(animations)
        flattened_animations = self.flatten(rescaled_animations)
        return flattened_animations

    def rescale_other(self, animations):
        """loops over passed animations and applies rescaling in case of attached relative run time"""
        rescaled_animations = []
        for animation in animations:
            if type(animation) is tuple:
                animation_tuple = animation  # is tuple
                animation, rel_run_time = animation_tuple  # unpack tuple
                if type(animation) is AnimationGroup:
                    animation_group = animation  # is animaiton group
                    animation_group.rescale_self(rel_run_time)
                elif type(animation) is Animation:
                    animation.rescale_relative_run_time(
                        rel_run_time)  # rescale relative run time
                # append to rescaled animations
                rescaled_animations.append(animation)
            elif issubclass(animation.__class__, (Animation, AnimationGroup)):
                # append to rescaled animations
                rescaled_animations.append(animation)
        return rescaled_animations

    def rescale_self(self, rel_run_time):
        """rescales animations contained in self"""
        for animation in self.animations:
            animation.rescale_relative_run_time(rel_run_time)

    def flatten(self, animations):
        """checks for and unpacks animation groups"""
        flattened_animations = []
        for animation in animations:
            if type(animation) is AnimationGroup:
                animation_group = animation  # is animation group
                # append to flattned input
                flattened_animations += animation_group.animations
            elif issubclass(animation.__class__, Animation):
                # append to flattened input
                flattened_animations.append(animation)
        return flattened_animations

    def execute(self):
        """executes all animations of the animation group"""
        for animation in self.animations:
            animation.execute()

    def get_objs(self):
        """retreives the objects contained in the animation group"""
        objs = []
        for animation in self.animations:
            target = animation.target
            if target.__class__.__name__ in ("SketchMaterial", "FillMaterial"):
                material = target  # is material
                obj = material.linked_tag.linked_object
            else:
                obj = target  # is object
            objs.append(obj)
        return objs

    def get_max_rel_stop(self):
        """retreives the relative stop value of the chronologically last animation of the group"""
        rel_stops = []
        for animation in self.animations:
            if type(animation) is VectorAnimation:
                rel_stops.append(animation.rel_stop)
            elif type(animation) is StateAnimation:
                # use relative start in case of state animation
                rel_stops.append(animation.rel_start)
        max_rel_stop = max(rel_stops)  # get maximum of relative stops
        return max_rel_stop

    def get_min_rel_start(self):
        """retreives the relative start value of the chronologically first animation of the group"""
        rel_starts = []
        for animation in self.animations:
            rel_starts.append(animation.rel_start)
        min_rel_start = min(rel_starts)  # get minimum of relative starts
        return min_rel_start

    def get_total_run_time(self):
        """retreives tuple of the first relative start and last relative stop value of the group"""
        min_rel_start = self.get_min_rel_start()
        max_rel_stop = self.get_max_rel_stop()
        return (min_rel_start, max_rel_stop)
