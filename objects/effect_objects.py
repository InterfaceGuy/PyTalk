from pydeation.objects.abstract_objects import CustomObject
from pydeation.objects.custom_objects import Text, Group
from pydeation.objects.solid_objects import Extrude
from pydeation.objects.line_objects import Arc, Circle, Rectangle, SplineText, Spline, PySpline
from pydeation.objects.sketch_objects import Human, Fire, Footprint
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

    def __init__(self, transition=False, **kwargs):
        self.transition = transition
        super().__init__(**kwargs)
        self.specify_action_interval()
        self.create_visibility_control()

    def specify_action_interval(self):
        self.action_interval = (0, 1)

    def create_visibility_control(self):
        self.specify_driving_parameter()
        self.specify_initial_objects()
        self.specify_final_objects()
        visibility_control = XVisibilityControl(target=self, driving_parameter=self.driving_parameter,
                                                initial_objects=self.initial_objects, final_objects=self.final_objects,
                                                invisibility_interval=self.action_interval)

    def specify_driving_parameter(self):
        self.driving_parameter = self.action_parameter

    def specify_initial_objects(self):
        self.initial_objects = [self.object_ini]

    def specify_final_objects(self):
        self.final_objects = [self.object_fin]


class Morpher(EffectObject):
    """creates a (set of) spline(s) depending on segment count that morphs between any two splines"""

    def __init__(self, object_ini, object_fin, morph_completion=0, linear_field_length=50, **kwargs):
        self.object_ini = object_ini
        self.object_fin = object_fin
        self.spline_ini = self.get_spline(object_ini)
        self.spline_fin = self.get_spline(object_fin)
        self.morph_completion = morph_completion
        self.linear_field_length = linear_field_length
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
        else:
            spline_object = input_object
        return spline_object

    def specify_action_interval(self):
        self.action_interval = (1 / 3, 2 / 3)

    def specify_parts(self):
        self.create_linear_field()
        self.create_spline_effectors()
        self.create_destination_splines()
        self.create_mosplines()
        self.parts += [self.linear_field, self.spline_effectors_ini,
                       self.spline_effectors_fin, self.mosplines, self.destination_splines]

    def create_linear_field(self):
        self.linear_field = LinearField(direction="x-")
        self.parts.append(self.linear_field)

    def create_spline_effectors(self):
        self.spline_effectors_ini = Group(*[SplineEffector(spline=self.spline_ini, segment_index=i, name=f"SplineEffector{i}")
                                            for i in range(self.segment_count_ini)], name="SplineEffectorsInitial")
        self.spline_effectors_fin = Group(*[SplineEffector(spline=self.spline_fin, fields=[self.linear_field], segment_index=i, name=f"SplineEffector{i}")
                                            for i in range(self.segment_count_fin)], name="SplineEffectorsFinal")

    def create_destination_splines(self):
        self.destination_splines = Group(
            *[Spline(name=f"DestinationSpline{i}", draw_completion=1) for i in range(self.segment_count)], name="DestinationSplines")

    def create_mosplines(self):
        self.mosplines = Group(*[MoSpline(source_spline=self.spline_ini, destination_spline=destination_spline, name=f"MoSpline{i}")
                                 for i, destination_spline in enumerate(self.destination_splines)], name="MoSplines")
        # we want to match the segments in the most natural way using modulu
        indices_ini, indices_fin = match_indices(
            self.segment_count_ini, self.segment_count_fin)
        for i, j, mospline in zip(indices_ini, indices_fin, self.mosplines):
            mospline.add_effector(self.spline_effectors_ini[i])
            mospline.add_effector(self.spline_effectors_fin[j])

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
        self.parameters += [self.morph_completion_parameter,
                            self.linear_field_length_parameter,
                            self.object_ini_fill_parameter,
                            self.object_fin_fill_parameter,
                            self.object_ini_width_parameter,
                            self.object_ini_center_x_parameter]

    def specify_relations(self):
        morph_completion_relation = XRelation(part=self.linear_field, whole=self, desc_ids=[POS_X], parameters=[self.morph_completion_parameter, self.linear_field_length_parameter, self.object_ini_width_parameter, self.object_ini_center_x_parameter],
                                              formula=f"{self.object_ini_center_x_parameter.name}-({self.object_ini_width_parameter.name}/2+{self.linear_field_length_parameter.name})+({self.object_ini_width_parameter.name}+2*{self.linear_field_length_parameter.name})*{self.morph_completion_parameter.name}")
        linear_field_length_relation = XIdentity(part=self.linear_field, whole=self, desc_ids=[self.linear_field.desc_ids["length"]],
                                                 parameter=self.linear_field_length_parameter)
        object_ini_fill_relation = XIdentity(part=self.object_ini, whole=self, desc_ids=[self.object_ini.fill_parameter.desc_id],
                                             parameter=self.object_ini_fill_parameter)
        object_fin_fill_relation = XIdentity(part=self.object_fin, whole=self, desc_ids=[self.object_fin.fill_parameter.desc_id],
                                             parameter=self.object_fin_fill_parameter)
        object_ini_width_inheritance = XIdentity(part=self, whole=self.object_ini, desc_ids=[self.object_ini_width_parameter.desc_id],
                                                 parameter=self.object_ini.width_parameter)
        object_ini_center_x_inheritance = XIdentity(part=self, whole=self.object_ini, desc_ids=[self.object_ini_center_x_parameter.desc_id],
                                                    parameter=self.object_ini.center_x_parameter)

    def specify_action_parameters(self):
        self.action_parameter = UCompletion(name="Morph", default_value=0)
        self.action_parameters = [self.action_parameter]

    def specify_actions(self):
        morph_action = XAction(
            Movement(self.object_ini_fill_parameter,
                     (0, 1 / 3), output=(1, 0)),
            Movement(self.morph_completion_parameter, (1 / 3, 2 / 3)),
            Movement(self.object_fin_fill_parameter, (2 / 3, 1)),
            target=self, completion_parameter=self.action_parameter, name="Morph")

    def morph(self, completion=1):
        """specifies the morph animation"""
        desc_id = self.action_parameter.desc_id
        animation = ScalarAnimation(
            target=self, descriptor=desc_id, value_fin=completion)
        return animation
