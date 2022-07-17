from pydeation.xpresso.xpresso import *
from pydeation.xpresso.userdata import *
from pydeation.constants import *
from abc import ABC, abstractmethod
import c4d


class XPression(ABC):
    """creates xpressions for a given xpresso tag"""

    def __init__(self, target, freeze_tag=False, composition_level=None):
        self.target = target
        self.freeze_tag = freeze_tag
        self.composition_level = composition_level
        self.nodes = []
        self.construct()

    @abstractmethod
    def construct():
        """analogous to scene class this function constructs the xpression"""
        pass


class XActiveRange(XPression):
    """xpression for checking if completion is in active range"""

    def construct(self):
        # create nodes
        compare_node_0 = XCompare(self.target, mode="!=", comparison_value=0)
        compare_node_1 = XCompare(self.target, mode="!=", comparison_value=1)
        bool_node = XBool(self.target, mode="AND")

        # group nodes
        self.xgroup = XGroup(compare_node_0, compare_node_1,
                             bool_node, name=self.__class__.__name__[1:])
        self.obj = self.xgroup.obj

        # create ports
        self.real_interface_in = self.obj.AddPort(
            c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.bool_interface_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)

        # connect ports
        self.real_interface_in.Connect(compare_node_0.obj.GetInPort(0))
        self.real_interface_in.Connect(compare_node_1.obj.GetInPort(0))
        compare_node_0.obj.GetOutPort(0).Connect(bool_node.obj.GetInPort(0))
        compare_node_1.obj.GetOutPort(0).Connect(bool_node.obj.GetInPort(1))
        bool_node.obj.GetOutPort(0).Connect(self.bool_interface_out)


class XNotDescending(XPression):
    """xpression for checking if completion is NOT descending"""

    def construct(self):
        # create nodes
        memory_node = XMemory(self.target)
        compare_node = XCompare(self.target, mode=">=")
        constant_node = XConstant(self.target, value=1)

        # group nodes
        self.xgroup = XGroup(memory_node, compare_node,
                             constant_node, name=self.__class__.__name__[1:])
        self.obj = self.xgroup.obj

        # create ports
        self.real_interface_in = self.obj.AddPort(
            c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.bool_interface_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)

        # connect ports
        self.real_interface_in.Connect(memory_node.obj.GetInPort(1))
        self.real_interface_in.Connect(compare_node.obj.GetInPort(0))
        memory_node.obj.GetOutPort(0).Connect(compare_node.obj.GetInPort(1))
        compare_node.obj.GetOutPort(0).Connect(self.bool_interface_out)
        constant_node.obj.GetOutPort(0).Connect(memory_node.obj.GetInPort(0))


class XOverrideController(XPression):
    """xgroup for checking if parameter should be overridden"""

    def construct(self):
        # create nodes
        active_range_node = XActiveRange(self.target)
        not_descending_node = XNotDescending(self.target)
        bool_node = XBool(self.target, mode="AND")

        # group nodes
        self.xgroup = XGroup(active_range_node, not_descending_node,
                             bool_node, name=self.__class__.__name__[1:])
        self.obj = self.xgroup.obj

        # create ports
        self.real_interface_in = self.obj.AddPort(
            c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.bool_interface_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)

        # connect ports
        self.real_interface_in.Connect(active_range_node.real_interface_in)
        self.real_interface_in.Connect(not_descending_node.real_interface_in)
        active_range_node.bool_interface_out.Connect(
            bool_node.obj.GetInPort(0))
        not_descending_node.bool_interface_out.Connect(
            bool_node.obj.GetInPort(1))
        bool_node.obj.GetOutPort(0).Connect(self.bool_interface_out)


class XInterpolator(XPression):
    """xpression for interpolating between two values using completion slider"""

    def construct(self):
        # create nodes
        self.formula_node = XFormula(self.target, variables=[
                                     "t", "ini", "fin"], formula="ini+t*(fin-ini)")

        # group nodes
        self.xgroup = XGroup(
            self.formula_node, name=self.__class__.__name__[1:])
        self.obj = self.xgroup.obj

        # create ports
        self.final_value_interface_in = self.obj.AddPort(
            c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.completion_interface_in = self.obj.AddPort(
            c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.output_interface_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, REAL_DESCID_OUT)

        # connect ports
        self.final_value_interface_in.Connect(
            self.formula_node.obj.GetInPort(2))
        self.completion_interface_in.Connect(
            self.formula_node.obj.GetInPort(0))
        self.formula_node.obj.GetOutPort(0).Connect(self.output_interface_out)

    def add_input_source(self, source=None):
        # create nodes
        object_node = XObject(self.target)

        # group nodes
        self.xgroup.add(object_node)

        # create ports
        initial_value_port = object_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, source.freeze_value.desc_id)

        # connect ports
        initial_value_port.Connect(self.formula_node.obj.GetInPort(1))


class XFreezer(XPression):
    """freezes the initial value in seperate xtag and writes it to udata for sharing it with main xtag"""

    def construct(self):
        # create nodes
        memory_node = XMemory(self.target, freeze_tag=self.freeze_tag)
        constant_node = XConstant(
            self.target, value=1, freeze_tag=self.freeze_tag)
        self.override_controller = XOverrideController(
            self.target, freeze_tag=self.freeze_tag)
        compare_node = XCompare(self.target, mode="<=",
                                freeze_tag=self.freeze_tag)
        self.freeze_node = XFreeze(self.target, freeze_tag=self.freeze_tag)

        # group nodes
        self.xgroup = XGroup(memory_node, constant_node, self.override_controller, compare_node,
                             self.freeze_node, name=self.__class__.__name__[1:], freeze_tag=self.freeze_tag)
        self.obj = self.xgroup.obj

        # connect ports
        self.override_controller.obj.GetOutPort(
            0).Connect(memory_node.obj.GetInPort(1))
        self.override_controller.obj.GetOutPort(
            0).Connect(compare_node.obj.GetInPort(0))
        memory_node.obj.GetOutPort(0).Connect(compare_node.obj.GetInPort(1))
        constant_node.obj.GetOutPort(0).Connect(memory_node.obj.GetInPort(0))
        compare_node.obj.GetOutPort(0).Connect(
            self.freeze_node.obj.GetInPort(0))

    def add_input_source(self, source=None, accessed_parameter=None, reverse_parameter_range=False):
        """adds the completion slider and the initial value udata to the freezer"""
        # create nodes
        object_node_out = XObject(self.target, freeze_tag=self.freeze_tag)
        object_node_in = XObject(self.target, freeze_tag=self.freeze_tag)
        accessed_parameter_node_out = XObject(
            self.target, link_target=accessed_parameter.link_target, freeze_tag=self.freeze_tag)
        if reverse_parameter_range:
            range_mapper_node = XRangeMapper(self.target, reverse=True)
            self.xgroup.add(range_mapper_node)

        # group nodes
        self.xgroup.add(object_node_out, object_node_in,
                        accessed_parameter_node_out)

        # create ports
        completion_port_out = object_node_out.obj.AddPort(
            c4d.GV_PORT_OUTPUT, source.completion_slider.desc_id)
        accessed_parameter_port_out = accessed_parameter_node_out.obj.AddPort(
            c4d.GV_PORT_OUTPUT, accessed_parameter.desc_id)
        freeze_value_port_in = object_node_in.obj.AddPort(
            c4d.GV_PORT_INPUT, source.freeze_value.desc_id)

        # connect ports
        completion_port_out.Connect(self.override_controller.real_interface_in)
        self.freeze_node.obj.GetOutPort(0).Connect(freeze_value_port_in)
        if reverse_parameter_range:
            accessed_parameter_port_out.Connect(
                range_mapper_node.obj.GetInPort(0))
            range_mapper_node.obj.GetOutPort(0).Connect(
                self.freeze_node.obj.GetInPort(1))
        else:
            accessed_parameter_port_out.Connect(
                self.freeze_node.obj.GetInPort(1))


class XAnimator(XPression):
    """template for generic xanimator that drives single parameter using a given formula"""

    def __init__(self, target, formula=None, variables=["t"], name=None, params=[], interpolate=False, composition_level=None):
        self.target = target
        self.obj_target = target.obj
        self.formula = formula
        self.variables = variables
        self.name = name
        self.udatas = [param[0] for param in params]  # get udata of parameters
        self.param_names = [param[1]
                            for param in params]  # get names of parameters
        # stores udatas and interpolation_target for animation
        self.animation_parameters = []
        self.interpolate = interpolate
        self.access_control = None
        self.composition_level = composition_level
        super().__init__(target, composition_level=self.composition_level)
        self.create_mapping()  # creates the mapping

    def construct(self):
        # create userdata
        uparams = []
        # completion slider
        self.completion_slider = UCompletion()
        uparams.append(self.completion_slider)
        # instantiate parameters
        for i, udata in enumerate(self.udatas):
            self.udatas[i] = udata(name=self.param_names[i])
        uparams += self.udatas
        # add to animation parameters
        self.animation_parameters = self.udatas
        # add interpolation target
        if self.interpolate:
            self.interpolation_target = UStrength(name="interpolation_target")
            self.freeze_value = UStrength(name="freeze_value")
            uparams += [self.interpolation_target, self.freeze_value]
            # add to animation parameters
            self.animation_parameters.append(self.interpolation_target)
        u_group = UGroup(*uparams, target=self.obj_target, name=self.name)

        # create nodes
        self.object_node = XObject(
            self.target, composition_level=self.composition_level)
        override_controller = XOverrideController(
            self.target, composition_level=self.composition_level)

        # group nodes
        self.xgroup = XGroup(self.object_node, override_controller, name=self.name + self.__class__.__name__[
                             1:], composition_level=self.composition_level)  # rip name from class name
        self.obj = self.xgroup.obj

        # create ports
        self.active_interface_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)
        self.completion_port_out = self.object_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.completion_slider.desc_id)
        if self.interpolate:
            self.final_interface_out = self.obj.AddPort(
                c4d.GV_PORT_OUTPUT, REAL_DESCID_OUT)
            strength_port_out = self.object_node.obj.AddPort(
                c4d.GV_PORT_OUTPUT, self.interpolation_target.desc_id)

        # connect ports
        self.completion_port_out.Connect(override_controller.real_interface_in)
        override_controller.bool_interface_out.Connect(
            self.active_interface_out)
        if self.interpolate:
            strength_port_out.Connect(self.final_interface_out)

    def create_mapping(self):
        """creates a mapping using the formula node"""
        # create nodes
        if self.interpolate:
            # this formula ensures that the output value is 1 at frame = frame_fin - 1
            self.formula = "ceil(t*round(1/(delta_t))*(1+delta_t))/round(1/(delta_t))"
            self.variables = ["t", "delta_t"]
            memory_node = XMemory(self.target)
            constant_node = XConstant(self.target, value=1)
            delta_node = XDelta(self.target)
        formula_node = XFormula(
            self.target, variables=self.variables, formula=self.formula)

        # group nodes
        if self.interpolate:
            self.xgroup.add(memory_node, constant_node, delta_node)
        self.xgroup.add(formula_node)

        # create ports
        self.driver_interface_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, REAL_DESCID_OUT)
        param_ports_out = []
        param_ports_in = []
        driver_port_out = formula_node.obj.GetOutPort(0)
        for udata, param_name in zip(self.udatas, self.param_names):
            param_port_out = self.object_node.obj.AddPort(
                c4d.GV_PORT_OUTPUT, udata.desc_id)
            param_ports_out.append(param_port_out)
            param_port_in = formula_node.obj.AddPort(
                c4d.GV_PORT_INPUT, VALUE_DESCID_IN)
            param_port_in.SetName(param_name)
            param_ports_in.append(param_port_in)

        # connect ports
        if self.interpolate:
            self.completion_port_out.Connect(memory_node.obj.GetInPort(1))
            constant_node.obj.GetOutPort(0).Connect(
                memory_node.obj.GetInPort(0))
            memory_node.obj.GetOutPort(0).Connect(delta_node.obj.GetInPort(1))
            self.completion_port_out.Connect(delta_node.obj.GetInPort(0))
            delta_node.obj.GetOutPort(0).Connect(
                formula_node.variable_ports["delta_t"])
        self.completion_port_out.Connect(formula_node.variable_ports["t"])
        driver_port_out.Connect(self.driver_interface_out)
        for param_port_in, param_port_out in zip(param_ports_in, param_ports_out):
            param_port_out.Connect(param_port_in)


class XComposer(XAnimator):
    """special kind of xanimator used for compositions, uses multiple range mappers instead of formula"""

    def create_mapping(self):
        """not used for xcomposer"""
        pass

    def add_range_mapping(self, input_range):
        """adds a range mapper node and an out port to the xpression"""
        # create nodes
        # this formula ensures that the output value is 1 at frame = frame_fin - 1
        formula = "ceil(t*round(1/(delta_t))*(1+delta_t))/round(1/(delta_t))"
        formula_node = XFormula(self.target, variables=[
                                "t", "delta_t"], formula=formula, composition_level=self.composition_level)
        constant_node = XConstant(
            self.target, value=1, composition_level=self.composition_level)
        memory_node = XMemory(
            self.target, composition_level=self.composition_level)
        range_mapper_node = XRangeMapper(
            self.target, input_range=input_range, composition_level=self.composition_level)
        delta_node = XDelta(
            self.target, composition_level=self.composition_level)

        # group nodes
        self.xgroup.add(formula_node, constant_node,
                        memory_node, range_mapper_node, delta_node)

        # create ports
        self.driver_interface_out = self.obj.AddPort(
            c4d.GV_PORT_OUTPUT, REAL_DESCID_OUT)

        # connect ports
        self.completion_port_out.Connect(formula_node.variable_ports["t"])
        self.completion_port_out.Connect(delta_node.obj.GetInPort(0))
        self.completion_port_out.Connect(memory_node.obj.GetInPort(1))
        constant_node.obj.GetOutPort(0).Connect(memory_node.obj.GetInPort(0))
        memory_node.obj.GetOutPort(0).Connect(delta_node.obj.GetInPort(1))
        formula_node.obj.GetOutPort(0).Connect(
            range_mapper_node.obj.GetInPort(0))
        range_mapper_node.obj.GetOutPort(0).Connect(self.driver_interface_out)
        delta_node.obj.GetOutPort(0).Connect(
            formula_node.variable_ports["delta_t"])


class XAccessControl(XPression):
    """xgroup for handling which input should override given parameter"""

    def __init__(self, target, parameter=None, link_target=None, reverse_parameter_range=False, composition_level=None):
        # input counter for adding input sources
        self.input_count = 0
        # specify link target
        self.link_target = link_target
        # specify if range mapper should be inserted before parameter
        self.reverse_parameter_range = reverse_parameter_range
        # specify to which xtag of the composition hierarchy the xpression should be applied
        self.composition_level = composition_level
        # check for xanimator
        if type(parameter) in (XAnimator, XComposer):
            xanimator = parameter  # is xanimator
            self.parameter = xanimator.completion_slider
            self.name = xanimator.name
        elif type(parameter) is UParameter:
            self.parameter = parameter
            self.name = parameter.name
            target = parameter.target
        else:
            raise TypeError(
                "parameter must be of type XAnimator, XComposer or UParameter!")
        super().__init__(target, composition_level=self.composition_level)

    def construct(self):
        # create nodes
        self.condition_switch_node = XConditionSwitch(
            self.target, composition_level=self.composition_level)
        self.condition_node = XCondition(
            self.target, composition_level=self.composition_level)
        object_node_out = XObject(
            self.target, link_target=self.link_target, composition_level=self.composition_level)
        object_node_in = XObject(
            self.target, link_target=self.link_target, composition_level=self.composition_level)
        nodes = [self.condition_switch_node,
                 self.condition_node, object_node_out, object_node_in]
        if self.reverse_parameter_range:
            self.range_mapper_node_in = XRangeMapper(
                self.target, reverse=True, composition_level=self.composition_level)
            self.range_mapper_node_out = XRangeMapper(
                self.target, reverse=True, composition_level=self.composition_level)
            optional_nodes = [self.range_mapper_node_in,
                              self.range_mapper_node_out]
            nodes += optional_nodes

        # group nodes
        self.xgroup = XGroup(*nodes, name=self.name + "AccessControl",
                             composition_level=self.composition_level)
        self.obj = self.xgroup.obj

        # create ports
        self.active_interfaces_in = []
        self.driver_interfaces_in = []
        self.parameter_port_out = object_node_out.obj.AddPort(
            c4d.GV_PORT_OUTPUT, self.parameter.desc_id)
        self.parameter_port_in = object_node_in.obj.AddPort(
            c4d.GV_PORT_INPUT, self.parameter.desc_id)

        # connect ports
        self.condition_switch_node.obj.GetOutPort(
            0).Connect(self.condition_node.obj.GetInPort(0))
        self.parameter_port_out.Connect(self.condition_node.obj.GetInPort(1))
        self.condition_node.obj.GetOutPort(0).Connect(self.parameter_port_in)
        if self.reverse_parameter_range:
            self.range_mapper_node_in.obj.GetOutPort(
                0).Connect(self.condition_node.obj.GetInPort(1))
            self.range_mapper_node_out.obj.GetOutPort(
                0).Connect(self.parameter_port_in)
            self.parameter_port_out.Connect(
                self.range_mapper_node_in.obj.GetInPort(0))
            self.condition_node.obj.GetOutPort(0).Connect(
                self.range_mapper_node_out.obj.GetInPort(0))

        # remove unused ports
        self.condition_switch_node.obj.RemoveUnusedPorts()
        self.condition_node.obj.RemoveUnusedPorts()

        # name ports
        self.condition_node.obj.GetInPort(1).SetName("Idle")

    def add_input_source(self, source, interpolate=False):
        """adds and connects a bool input and a real input to a given input source"""
        # update input count
        self.input_count += 1

        # create ports
        self.active_interfaces_in.append(
            self.obj.AddPort(c4d.GV_PORT_INPUT, BOOL_DESCID_IN))
        self.driver_interfaces_in.append(
            self.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN))
        new_condition_switch_port_in = self.condition_switch_node.obj.AddPort(
            c4d.GV_PORT_INPUT, CONDITION_SWITCH_DESCID_IN)
        new_condition_port_in = self.condition_node.obj.AddPort(
            c4d.GV_PORT_INPUT, CONDITION_DESCID_IN)

        # connect ports
        # interior
        self.active_interfaces_in[-1].Connect(new_condition_switch_port_in)
        self.driver_interfaces_in[-1].Connect(new_condition_port_in)
        # exterior
        source.active_interface_out.Connect(self.active_interfaces_in[-1])
        source.driver_interface_out.Connect(self.driver_interfaces_in[-1])

        # name ports
        new_condition_switch_port_in.SetName("Input" + str(self.input_count))
        new_condition_port_in.SetName("Input" + str(self.input_count))

        # optionally interpose interpolator
        if interpolate:
            self.interpose_interpolator(
                source, self.driver_interfaces_in[-1], new_condition_port_in)

    def interpose_interpolator(self, source, completion_source, output_target):
        """interposes an interpolator for linear interpolation between initial and final value of target parameter"""
        # create nodes
        interpolator = XInterpolator(
            self.target, composition_level=self.composition_level)
        interpolator.add_input_source(source=source)
        freezer = XFreezer(self.target, freeze_tag=True)
        freezer.add_input_source(source=source, accessed_parameter=self.parameter,
                                 reverse_parameter_range=self.reverse_parameter_range)

        # group nodes
        self.xgroup.add(interpolator)

        # create ports
        final_source = self.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN)

        # connect ports
        final_source.Connect(interpolator.final_value_interface_in)
        source.final_interface_out.Connect(final_source)
        completion_source.Connect(interpolator.completion_interface_in)
        interpolator.output_interface_out.Connect(output_target)


class XComposition(XPression):
    """template for generic composed xanimator"""

    def __init__(self, *xanimator_tuples, target=None, name=None, composition_mode=False, composition_level=1):
        self.xanimator_tuples = xanimator_tuples
        self.target = target
        self.obj_target = target.obj
        self.name = name
        self.composition_mode = composition_mode
        self.composition_level = composition_level
        super().__init__(target, composition_level=self.composition_level)

    def construct(self):
        # unpack tuples
        self.xanimators = [xanimator_tuple[0]
                           for xanimator_tuple in self.xanimator_tuples]
        input_ranges = [xanimator_tuple[1]
                        for xanimator_tuple in self.xanimator_tuples]
        # create xcomposer
        self.xcomposer = XComposer(
            self.target, name=self.name, composition_level=self.composition_level)
        self.completion_slider = self.xcomposer.completion_slider
        # create access controls
        for xanimator, input_range in zip(self.xanimators, input_ranges):
            if xanimator.access_control is None:  # add access control if needed
                xanimator.access_control = XAccessControl(
                    self.target, parameter=xanimator, composition_level=self.composition_level)
            self.xcomposer.add_range_mapping(input_range)
            xanimator.access_control.add_input_source(self.xcomposer)
            # remember animation parameters of xanimators in case of composition mode
            if self.composition_mode:
                self.xcomposer.animation_parameters += xanimator.animation_parameters


class XAnimation(XPression):
    """connects xanimators to layer zero parameter"""

    def __init__(self, *xanimators, target=None, parameter=None, name=None, reverse_parameter_range=False):
        self.target = target
        self.xanimators = xanimators
        self.parameter = parameter
        self.obj_target = target.obj
        self.name = name
        self.reverse_parameter_range = reverse_parameter_range
        super().__init__(target)

    def construct(self):
        # create access controls if needed
        for xanimator in self.xanimators:
            if self.parameter.access_control is None:
                self.parameter.access_control = XAccessControl(
                    self.target, parameter=self.parameter, link_target=self.parameter.link_target, reverse_parameter_range=self.reverse_parameter_range)
            self.parameter.access_control.add_input_source(
                xanimator, interpolate=xanimator.interpolate)


class CustomXPression(XPression):

    def group_nodes(self):
        self.xgroup = XGroup(*self.nodes, custom_tag=True,
                             name=self.__class__.__name__)
        self.obj = self.xgroup.obj


class XRelation(CustomXPression):
    """creates a relation between a parameter of a part and the whole of a CustomObject"""

    def __init__(self, part=None, whole=None, desc_id=None, parameters=None, formula=None):
        self.formula = formula
        self.desc_id = desc_id
        self.parameters = parameters
        self.part = part
        self.whole = whole
        self.nodes = []
        super().__init__(self.whole)

    def construct(self):
        self.create_part_node()
        self.create_whole_node()
        self.create_formula_node()
        self.group_nodes()
        self.connect_ports()

    def create_part_node(self):
        self.part_node = XObject(self.whole, link_target=self.part)
        self.part_node.obj.AddPort(c4d.GV_PORT_INPUT, self.desc_id)
        self.nodes.append(self.part_node)

    def create_whole_node(self):
        self.whole_node = XObject(self.whole)
        for parameter in self.parameters:
            self.whole_node.obj.AddPort(c4d.GV_PORT_OUTPUT, parameter.desc_id)
        self.nodes.append(self.whole_node)

    def create_formula_node(self):
        self.formula_node = XFormula(
            self.whole, variables=[parameter.name for parameter in self.parameters], formula=self.formula)
        self.nodes.append(self.formula_node)

    def connect_ports(self):
        for formula_in_port, parameter_port_out in zip(self.formula_node.obj.GetInPorts(), self.whole_node.obj.GetOutPorts()):
            parameter_port_out.Connect(formula_in_port)
        self.formula_node.obj.GetOutPort(
            0).Connect(self.part_node.obj.GetInPort(0))


class XIdentity(XRelation):
    """creates a direct connection between a parameter of a part and the whole of a CustomObject"""

    def __init__(self, parameter=None, **kwargs):
        super().__init__(parameters=[parameter], **kwargs)

    def construct(self):
        self.create_part_node()
        self.create_whole_node()
        self.group_nodes()
        self.connect_ports()

    def connect_ports(self):
        self.whole_node.obj.GetOutPort(0).Connect(
            self.part_node.obj.GetInPort(0))


class XClosestPointOnSpline(CustomXPression):
    """creates a setup that positions a point on a spline such that the distance to a reference point is minimised"""

    def __init__(self, reference_point=None, spline_point=None, target=None, spline=None):
        self.spline = spline
        self.spline_point = spline_point
        self.reference_point = reference_point
        super().__init__(target)

    def construct(self):
        self.create_spline_node()
        self.create_reference_point_node()
        self.create_spline_point_node()
        self.create_nearest_point_on_spline_node()
        self.create_math_nodes()
        self.group_nodes()
        self.connect_ports()

    def create_spline_node(self):
        self.spline_node = XObject(self.target, link_target=self.spline)
        self.spline_node.obj.AddPort(c4d.GV_PORT_OUTPUT, OBJECT_DESCID_OUT)
        self.spline_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.ID_BASEOBJECT_GLOBAL_POSITION)
        self.nodes.append(self.spline_node)

    def create_reference_point_node(self):
        self.reference_point_node = XObject(
            self.target, link_target=self.reference_point)
        self.reference_point_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.ID_BASEOBJECT_GLOBAL_POSITION)
        self.nodes.append(self.reference_point_node)

    def create_spline_point_node(self):
        self.spline_point_node = XObject(
            self.target, link_target=self.spline_point)
        self.spline_point_node.obj.AddPort(
            c4d.GV_PORT_INPUT, c4d.ID_BASEOBJECT_REL_POSITION)
        self.nodes.append(self.spline_point_node)

    def create_nearest_point_on_spline_node(self):
        self.nearest_point_on_spline_node = XNearestPointOnSpline(self.target)
        self.nodes.append(self.nearest_point_on_spline_node)

    def create_math_nodes(self):
        self.add_node = XMath(self.target, mode="+", data_type="vector")
        self.substract_node = XMath(self.target, mode="-", data_type="vector")
        self.nodes += [self.add_node, self.substract_node]

    def connect_ports(self):
        self.spline_node.obj.GetOutPort(0).Connect(
            self.nearest_point_on_spline_node.obj.GetInPort(0))
        self.spline_node.obj.GetOutPort(1).Connect(
            self.substract_node.obj.GetInPort(1))
        self.spline_node.obj.GetOutPort(1).Connect(
            self.add_node.obj.GetInPort(0))
        self.reference_point_node.obj.GetOutPort(0).Connect(
            self.substract_node.obj.GetInPort(0))
        self.nearest_point_on_spline_node.obj.GetOutPort(1).Connect(
            self.add_node.obj.GetInPort(1))
        self.substract_node.obj.GetOutPort(0).Connect(
            self.nearest_point_on_spline_node.obj.GetInPort(1))
        self.add_node.obj.GetOutPort(0).Connect(
            self.spline_point_node.obj.GetInPort(0))


class XScaleBetweenPoints(CustomXPression):
    """creates a setup that scales adn positions an object such that it touches two points on its periphery"""

    def __init__(self, scaled_object=None, point_a=None, point_b=None, target=None):
        self.scaled_object = scaled_object
        self.point_a = point_a
        self.point_b = point_b
        super().__init__(target)

    def construct(self):
        self.create_distance_node()
        self.create_mix_node()
        self.create_divide_node()
        self.create_point_nodes()
        self.create_scaled_object_node()
        self.group_nodes()
        self.connect_ports()

    def create_distance_node(self):
        self.distance_node = XDistance(self.target)
        self.nodes.append(self.distance_node)

    def create_mix_node(self):
        self.mix_node = XMix(self.target, data_type="vector")
        self.nodes.append(self.mix_node)

    def create_divide_node(self):
        self.divide_node = XMath(self.target, mode="/")
        self.constant_node = XConstant(self.target, value=2)
        self.nodes += [self.divide_node, self.constant_node]

    def create_point_nodes(self):
        self.point_a_node = XObject(self.target, link_target=self.point_a)
        self.point_a_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.ID_BASEOBJECT_GLOBAL_POSITION)
        self.point_b_node = XObject(self.target, link_target=self.point_b)
        self.point_b_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, c4d.ID_BASEOBJECT_GLOBAL_POSITION)
        self.nodes += [self.point_a_node, self.point_b_node]

    def create_scaled_object_node(self):
        self.scaled_object_node = XObject(
            self.target, link_target=self.scaled_object)
        self.scaled_object_node_global_position_port = self.scaled_object_node.obj.AddPort(
            c4d.GV_PORT_INPUT, c4d.ID_BASEOBJECT_GLOBAL_POSITION)
        self.scaled_object_node_size_port = self.scaled_object_node.obj.AddPort(
            c4d.GV_PORT_INPUT, c4d.SPHERICAL_SIZE)
        self.nodes.append(self.scaled_object_node)

    def connect_ports(self):
        self.point_a_node.obj.GetOutPort(0).Connect(
            self.distance_node.obj.GetInPort(0))
        self.point_b_node.obj.GetOutPort(0).Connect(
            self.distance_node.obj.GetInPort(1))
        self.point_a_node.obj.GetOutPort(0).Connect(
            self.mix_node.obj.GetInPort(1))
        self.point_b_node.obj.GetOutPort(0).Connect(
            self.mix_node.obj.GetInPort(2))
        self.distance_node.obj.GetOutPort(0).Connect(
            self.divide_node.obj.GetInPort(0))
        self.divide_node.obj.GetOutPort(0).Connect(
            self.scaled_object_node_size_port)
        self.mix_node.obj.GetOutPort(0).Connect(
            self.scaled_object_node_global_position_port)
        self.constant_node.obj.GetOutPort(0).Connect(
            self.divide_node.obj.GetInPort(1))
