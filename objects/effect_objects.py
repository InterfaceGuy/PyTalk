from pydeation.objects.abstract_objects import CustomObject
from pydeation.objects.custom_objects import Text, Group
from pydeation.objects.solid_objects import Extrude
from pydeation.objects.line_objects import Arc, Circle, Rectangle, SplineText, Spline, PySpline
from pydeation.objects.sketch_objects import Human, Fire, Footprint, Sketch
from pydeation.objects.helper_objects import *
from pydeation.xpresso.userdata import UAngle, UGroup, ULength, UOptions, UCompletion, UText, UStrength, UCount
from pydeation.xpresso.xpressions import *
from pydeation.animation.animation import ScalarAnimation
from pydeation.constants import *
from pydeation.utils import match_indices
import c4d


class EffectObject(CustomObject):
    """an effect object has the additional ability to toggle the visibility of the objects it affects
        (like a stuntman telling the actor to go off stage for the stunt)"""

    def __init__(self, clone=False, **kwargs):
        self.clone = clone
        super().__init__(**kwargs)
        self.specify_action_interval()
        self.create_visibility_control()

    def specify_action_interval(self):
        self.action_interval = (0, 1)

    def create_visibility_control(self):
        self.specify_driving_parameter()
        self.specify_initial_objects()
        self.specify_final_objects()
        if self.clone:
            visibility_control = XVisibilityControl(target=self, driving_parameter=self.driving_parameter,
                                                    initial_objects=[], transition_objects=[
                                                        self], final_objects=self.final_objects,
                                                    invisibility_interval=self.action_interval)
        else:
            visibility_control = XVisibilityControl(target=self, driving_parameter=self.driving_parameter,
                                                    initial_objects=self.initial_objects, transition_objects=[
                                                        self], final_objects=self.final_objects,
                                                    invisibility_interval=self.action_interval)

    def specify_driving_parameter(self):
        self.driving_parameter = self.action_parameter

    def specify_initial_objects(self):
        self.initial_objects = [self.object_ini]

    def specify_final_objects(self):
        self.final_objects = [self.object_fin]


class Segment:

    def __init__(self, length):
        self.length = length
        self.sub_segments = 1

    def get_length(self):
        return self.length/self.sub_segments


class Morpher(EffectObject):
    """creates a (set of) spline(s) depending on segment count that morphs between any two spline objects"""

    def __init__(self, object_ini, object_fin, morph_completion=0, linear_field_length=50, mode="linear", **kwargs):
        self.object_ini = object_ini
        self.object_fin = object_fin
        self.spline_ini = self.get_spline(object_ini)
        self.spline_fin = self.get_spline(object_fin)
        self.morph_completion = morph_completion
        self.linear_field_length = linear_field_length
        self.mode = mode
        self.get_segment_counts()
        super().__init__(**kwargs)

    def set_name(self, name=None):
        self.name = f"Morph:{self.spline_ini.name}->{self.spline_fin.name}"
        self.obj.SetName(self.name)

    def get_segment_counts(self):
        self.segment_count_ini = self.spline_ini.get_segment_count()
        self.segment_count_fin = self.spline_fin.get_segment_count()
        self.segment_count = max(
            self.segment_count_ini, self.segment_count_fin)



    def get_spline(self, input_object):
        if type(input_object) is Text:
            spline_object = input_object.spline_text
        elif issubclass(input_object.__class__, Sketch):
            spline_object = input_object.svg
        else:
            spline_object = input_object
        return spline_object

    def specify_action_interval(self):
        if hasattr(self.object_ini, "fill_parameter") and hasattr(self.object_fin, "fill_parameter"):
            self.action_interval = (1 / 3, 2 / 3)
        elif hasattr(self.object_ini, "fill_parameter"):
            self.action_interval = (1 / 3, 1)
        elif hasattr(self.object_fin, "fill_parameter"):
            self.action_interval = (0, 2 / 3)
        else:
            self.action_interval = (0, 1)

    def specify_parts(self):
        if self.mode == "linear":
            self.create_linear_field()
            self.parts.append(self.linear_field)
        self.subdivide_segments()
        self.create_spline_effectors()
        self.create_destination_splines()
        self.create_mosplines()
        self.parts += [self.spline_effectors_ini,
                       self.spline_effectors_fin, self.mosplines, self.destination_splines]

    def create_linear_field(self):
        self.linear_field = LinearField(direction="x-")
        self.parts.append(self.linear_field)


    def subdivide_segments(self):
        # subdivides the segments to match the segment counts of both splines

        def get_longest_segment_index(segments):
            # get index of the longest segment
            longest_segment_index = 0
            longest_segment_length = 0
            for i, segment in enumerate(segments):
                if segment.get_length() > longest_segment_length:
                    longest_segment_length = segment.get_length()
                    longest_segment_index = i
            return longest_segment_index


        if self.segment_count_ini <= self.segment_count_fin:
            # subdivide initial spline segments
            segment_lengths = self.spline_ini.get_spline_segment_lengths()
            number_segments = self.spline_ini.get_segment_count()
            number_segments_other = self.spline_fin.get_segment_count()
        elif self.segment_count_ini > self.segment_count_fin:
            # subdivide final spline segments
            segment_lengths = self.spline_fin.get_spline_segment_lengths()
            number_segments = self.spline_fin.get_segment_count()
            number_segments_other = self.spline_ini.get_segment_count()

        self.segments = [Segment(length=segment_length) for segment_length in segment_lengths]
        
        while number_segments < number_segments_other:
            longest_segment_idx = get_longest_segment_index(self.segments)
            self.segments[longest_segment_idx].sub_segments += 1
            number_segments += 1


    def create_spline_effectors(self):
        if self.mode == "linear":
            fields = [self.linear_field]
        else:
            fields = []

        if self.segment_count_ini < self.segment_count_fin:
            # subdivide initial spline segments
            segment_lengths_fin = self.spline_fin.get_spline_segment_lengths()
            self.spline_effectors_fin = Group(*[SplineEffector(spline=self.spline_fin, fields=fields, segment_index=i, name=f"SplineEffector{i}")
                                                for i in range(len(segment_lengths_fin))], name="SplineEffectorsFinal")
            self.spline_effectors_ini = Group(name="SplineEffectorsInitial")
            for i, segment in enumerate(self.segments):
                for j in range(segment.sub_segments):
                    offset_start = 1/segment.sub_segments*j
                    offset_end = 1 - 1/segment.sub_segments*(j+1)
                    self.spline_effectors_ini.add(SplineEffector(spline=self.spline_ini, segment_index=i, offset_start=offset_start, offset_end=offset_end, name=f"SplineEffector{i}.{j}"))

        elif self.segment_count_ini > self.segment_count_fin:
            # subdivide final spline segments
            segment_lengths_ini = self.spline_ini.get_spline_segment_lengths()
            self.spline_effectors_ini = Group(*[SplineEffector(spline=self.spline_ini, fields=fields, segment_index=i, name=f"SplineEffector{i}")
                                                for i in range(len(segment_lengths_ini))], name="SplineEffectorsInitial")
            self.spline_effectors_fin = Group(name="SplineEffectorsFinal")
            for i, segment in enumerate(self.segments):
                for j in range(segment.sub_segments):
                    offset_start = 1/segment.sub_segments*j
                    offset_end = 1 - 1/segment.sub_segments*(j+1)
                    self.spline_effectors_fin.add(SplineEffector(spline=self.spline_fin, segment_index=i, offset_start=offset_start, offset_end=offset_end, name=f"SplineEffector{i}.{j}"))

        else:
            self.spline_effectors_ini = Group(*[SplineEffector(spline=self.spline_ini, fields=fields, segment_index=i, name=f"SplineEffector{i}")
                                                for i in range(self.segment_count_ini)], name="SplineEffectorsInitial")
            self.spline_effectors_fin = Group(*[SplineEffector(spline=self.spline_fin, fields=fields, segment_index=i, name=f"SplineEffector{i}")
                                                for i in range(self.segment_count_fin)], name="SplineEffectorsFinal")

    def create_destination_splines(self):
        self.destination_splines = Group(
            *[Spline(name=f"DestinationSpline{i}", creation=True) for i in range(self.segment_count)], name="DestinationSplines")

    def create_mosplines(self):
        self.mosplines = Group(*[VisibleMoSpline(source_spline=self.spline_ini, name=f"MoSpline{i}", creation=True)
                                 for i in range(self.segment_count)], name="MoSplines")
        
        # we sort the spline effectors by effective length
        self.spline_effectors_ini.sort(key=lambda effector: effector.effective_length)
        self.spline_effectors_fin.sort(key=lambda effector: effector.effective_length)

        for i, mospline in enumerate(self.mosplines):
            mospline.add_effector(self.spline_effectors_ini[i])
            mospline.add_effector(self.spline_effectors_fin[i])

    def specify_parameters(self):
        self.morph_completion_parameter = UCompletion(
            name="MorphCompletionParameter", default_value=self.morph_completion)
        self.linear_field_length_parameter = ULength(
            name="FieldLengthParameter", default_value=self.linear_field_length)
        self.object_ini_fill_parameter = UCompletion(
            name="ObjectIniFillParameter")
        self.object_fin_fill_parameter = UCompletion(
            name="ObjectFinFillParameter")
        self.object_ini_width_parameter = ULength(
            name="ObjectIniWidthParameter")
        self.object_ini_center_x_parameter = ULength(
            name="ObjectIniPositionXParameter")
        self.object_ini_color_parameter = UColor(
            name="ObjectIniColorParameter", default_value=self.object_ini.color)
        self.object_fin_color_parameter = UColor(
            name="ObjectFinColorParameter", default_value=self.object_fin.color)
        self.color_blend_parameter = UCompletion(
            name="ColorBlendParameter")
        self.parameters += [self.morph_completion_parameter,
                            self.linear_field_length_parameter,
                            self.object_ini_fill_parameter,
                            self.object_fin_fill_parameter,
                            self.object_ini_width_parameter,
                            self.object_ini_center_x_parameter,
                            self.object_ini_color_parameter,
                            self.object_fin_color_parameter,
                            self.color_blend_parameter]

    def specify_relations(self):
        if self.mode == "linear":
            morph_completion_relation = XRelation(part=self.linear_field, whole=self, desc_ids=[POS_X], parameters=[self.morph_completion_parameter, self.linear_field_length_parameter, self.object_ini_width_parameter, self.object_ini_center_x_parameter],
                                                  formula=f"{self.object_ini_center_x_parameter.name}-({self.object_ini_width_parameter.name}/2+{self.linear_field_length_parameter.name})+({self.object_ini_width_parameter.name}+2*{self.linear_field_length_parameter.name})*{self.morph_completion_parameter.name}")
            linear_field_length_relation = XIdentity(part=self.linear_field, whole=self, desc_ids=[self.linear_field.desc_ids["length"]],
                                                     parameter=self.linear_field_length_parameter)
        elif self.mode == "constant":
            for spline_effector_fin in self.spline_effectors_fin:
                morph_completion_relation = XIdentity(part=spline_effector_fin, whole=self, desc_ids=[spline_effector_fin.desc_ids["strength"]],
                                                      parameter=self.morph_completion_parameter)
        if hasattr(self.object_ini, "fill_parameter"):
            object_ini_fill_relation = XIdentity(part=self.object_ini, whole=self, desc_ids=[self.object_ini.fill_parameter.desc_id],
                                                 parameter=self.object_ini_fill_parameter)
        if hasattr(self.object_fin, "fill_parameter"):
            object_fin_fill_relation = XIdentity(part=self.object_fin, whole=self, desc_ids=[self.object_fin.fill_parameter.desc_id],
                                                 parameter=self.object_fin_fill_parameter)
        object_ini_width_inheritance = XIdentity(part=self, whole=self.object_ini, desc_ids=[self.object_ini_width_parameter.desc_id],
                                                 parameter=self.object_ini.width_parameter)
        object_ini_center_x_inheritance = XIdentity(part=self, whole=self.object_ini, desc_ids=[self.object_ini_center_x_parameter.desc_id],
                                                    parameter=self.object_ini.center_x_parameter)
        color_blend_relation = XColorBlend(target=self, blend_parameter=self.color_blend_parameter,
                                           color_ini_parameter=self.object_ini_color_parameter, color_fin_parameter=self.object_fin_color_parameter)

    def specify_action_parameters(self):
        self.action_parameter = UCompletion(name="Morph", default_value=0)
        self.action_parameters = [self.action_parameter]

    def specify_actions(self):
        if hasattr(self.object_ini, "fill_parameter") and hasattr(self.object_fin, "fill_parameter"):
            morph_action = XAction(
                Movement(self.object_ini.fill_parameter,
                         (0, 1 / 3), output=(1, 0), part=self.object_ini),
                Movement(self.morph_completion_parameter, (1 / 3, 2 / 3)),
                Movement(self.color_blend_parameter, (1 / 3, 2 / 3)),
                Movement(self.object_fin.fill_parameter, (2 / 3, 1), part=self.object_fin),
                target=self, completion_parameter=self.action_parameter, name="Morph")
        elif hasattr(self.object_ini, "fill_parameter"):
            morph_action = XAction(
                Movement(self.object_ini.fill_parameter,
                         (0, 1 / 3), output=(1, 0), part=self.object_ini),
                Movement(self.morph_completion_parameter, (1 / 3, 1)),
                Movement(self.color_blend_parameter, (1 / 3, 1)),
                target=self, completion_parameter=self.action_parameter, name="Morph")
        elif hasattr(self.object_fin, "fill_parameter"):
            morph_action = XAction(
                Movement(self.morph_completion_parameter, (0, 2 / 3)),
                Movement(self.color_blend_parameter, (0, 2 / 3)),
                Movement(self.object_fin.fill_parameter, (2 / 3, 1), part=self.object_fin),
                target=self, completion_parameter=self.action_parameter, name="Morph")
        else:
            morph_action = XAction(
                Movement(self.morph_completion_parameter, (0, 1)),
                Movement(self.color_blend_parameter, (1 / 2, 1)),
                target=self, completion_parameter=self.action_parameter, name="Morph")

    def morph(self, completion=1):
        """specifies the morph animation"""
        desc_id = self.action_parameter.desc_id
        animation = ScalarAnimation(
            target=self, descriptor=desc_id, value_fin=completion)
        return animation
