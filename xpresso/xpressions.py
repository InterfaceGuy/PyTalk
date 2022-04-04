from pydeation.xpresso.xpresso import *
from pydeation.xpresso.userdata import *
from pydeation.constants import *
import c4d


class XActiveRange(XPression):
    """xpression for checking if completion is in active range"""

    def construct(self):
        # create nodes
        compare_node_0 = XCompare(self.target, mode="!=", comparison_value=0)
        compare_node_1 = XCompare(self.target, mode="!=", comparison_value=1)
        bool_node = XBool(self.target, mode="AND")
        
        # group nodes
        self.xgroup = XGroup(compare_node_0, compare_node_1,
                                 bool_node, name="InActiveRange")
        self.obj = self.xgroup.obj
        
        # create ports
        self.real_interface_in = self.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.bool_interface_out = self.obj.AddPort(c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)
        
        # connect ports
        compare_port_0_in = compare_node_0.obj.GetInPort(0)
        compare_port_1_in = compare_node_1.obj.GetInPort(0)
        compare_port_0_out = compare_node_0.obj.GetOutPort(0)
        compare_port_1_out = compare_node_1.obj.GetOutPort(0)
        bool_ports_in = bool_node.obj.GetInPorts()
        bool_port_out = bool_node.obj.GetOutPort(0)
        self.real_interface_in.Connect(compare_port_0_in)
        self.real_interface_in.Connect(compare_port_1_in)
        compare_port_0_out.Connect(bool_ports_in[0])
        compare_port_1_out.Connect(bool_ports_in[1])
        bool_port_out.Connect(self.bool_interface_out)


class XNotDescending(XPression):
    """xpression for checking if completion is NOT descending"""

    def construct(self):
        # create nodes
        memory_node = XMemory(self.target)
        compare_node = XCompare(self.target, mode=">=")
        constant_node = XConstant(self.target, value=1)

        # group nodes
        self.xgroup = XGroup(memory_node, compare_node, constant_node, name="NotDescending")
        self.obj = self.xgroup.obj

        # create ports
        self.real_interface_in = self.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.bool_interface_out = self.obj.AddPort(c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)

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
        memory_node = XMemory(self.target)
        constant_node = XConstant(self.target, value=1)
        not_descending_node = XNotDescending(self.target)
        bool_node = XBool(self.target, mode="AND")

        # group nodes
        self.xgroup = XGroup(active_range_node, memory_node, constant_node, not_descending_node, bool_node, name="OverrideController")
        self.obj = self.xgroup.obj

        # create ports
        self.real_interface_in = self.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.bool_interface_out = self.obj.AddPort(c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)

        # connect ports
        self.real_interface_in.Connect(active_range_node.real_interface_in)
        self.real_interface_in.Connect(not_descending_node.real_interface_in)
        active_range_node.bool_interface_out.Connect(memory_node.obj.GetInPort(1))
        memory_node.obj.GetOutPort(0).Connect(bool_node.obj.GetInPort(0))
        constant_node.obj.GetOutPort(0).Connect(memory_node.obj.GetInPort(0))
        not_descending_node.bool_interface_out.Connect(bool_node.obj.GetInPort(1))
        bool_node.obj.GetOutPort(0).Connect(self.bool_interface_out)


class XInterpolator(XPression):
    """xpression for interpolating between two values using completion slider"""

    def construct(self):
        # create nodes
        memory_node = XMemory(self.target, history_level=1)
        override_controller = XOverrideController(self.target)
        compare_node = XCompare(self.target, mode="<")
        freeze_node = XFreeze(self.target)
        formula_node = XFormula(self.target, variables=["t","ini","fin"], formula="ini+t*(fin-ini)")

        # group nodes
        self.xgroup = XGroup(memory_node, override_controller, compare_node, freeze_node, formula_node, name="Interpolator")
        self.obj = self.xgroup.obj

        # create ports
        self.ini_interface_in = self.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.fin_interface_in = self.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.completion_interface_in = self.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.output_interface_out = self.obj.AddPort(c4d.GV_PORT_OUTPUT, REAL_DESCID_OUT)

        # connect ports
        self.ini_interface_in.Connect(freeze_node.obj.GetInPort(1))
        self.fin_interface_in.Connect(formula_node.obj.GetInPort(2))
        self.completion_interface_in.Connect(override_controller.obj.GetInPort(0))
        self.completion_interface_in.Connect(formula_node.obj.GetInPort(0))
        override_controller.obj.GetOutPort(0).Connect(memory_node.obj.GetInPort(1))
        override_controller.obj.GetOutPort(0).Connect(compare_node.obj.GetInPort(0))
        memory_node.obj.GetOutPort(0).Connect(compare_node.obj.GetInPort(1))
        compare_node.obj.GetOutPort(0).Connect(freeze_node.obj.GetInPort(0))
        freeze_node.obj.GetOutPort(0).Connect(formula_node.obj.GetInPort(1))
        formula_node.obj.GetOutPort(0).Connect(self.output_interface_out)


class XAnimator(XPression):
    """template for generic animator that drives single parameter using a given formula"""

    def __init__(self, target, formula=None, name=None, params=[], interpolate=False):
        self.target = target
        self.obj_target = target.obj
        self.formula = formula
        self.name = name
        self.udatas = [param[0] for param in params]  # get udata of parameters
        self.param_names = [param[1] for param in params]  # get udata of parameters
        self.interpolate = interpolate
        self.access_control = None
        super().__init__(target)
        self.create_mapping()  # creates the mapping

    def construct(self):
        # create userdata
        uparams = []
        # completion slider
        self.completion_slider = UCompletion()
        uparams.append(self.completion_slider)
        # parameters
        for i, udata in enumerate(self.udatas):
            self.udatas[i] = udata(name=self.param_names[i])
        uparams += self.udatas
        # interpolate
        if self.interpolate:
            self.strength = UStrength()
            uparams.append(self.strength)
        u_group = UGroup(*uparams, target=self.obj_target, name=self.name)

        # create nodes
        self.object_node = XObject(self.target)
        override_controller = XOverrideController(self.target)
        
        # group nodes
        self.xgroup = XGroup(self.object_node, override_controller, name=self.name+"Animator")
        self.obj = self.xgroup.obj

        # create ports
        self.active_interface_out = self.obj.AddPort(c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)
        self.completion_port_out = self.object_node.obj.AddPort(c4d.GV_PORT_OUTPUT, self.completion_slider.desc_id)
        if self.interpolate:
            self.final_interface_out = self.obj.AddPort(c4d.GV_PORT_OUTPUT, REAL_DESCID_OUT)
            strength_port_out = self.object_node.obj.AddPort(c4d.GV_PORT_OUTPUT, self.strength.desc_id)

        # connect ports
        self.completion_port_out.Connect(override_controller.real_interface_in)
        override_controller.bool_interface_out.Connect(self.active_interface_out)
        if self.interpolate:
            strength_port_out.Connect(self.final_interface_out)


    def create_mapping(self):
        """creates a mapping using the formula node"""
        # create nodes
        formula_node = XFormula(self.target, formula=self.formula)

        # group nodes
        self.xgroup.add(formula_node)
        
        # create ports
        self.driver_interface_out = self.obj.AddPort(c4d.GV_PORT_OUTPUT, REAL_DESCID_OUT)
        param_ports_out = []
        param_ports_in = []
        t_port = formula_node.obj.AddPort(c4d.GV_PORT_INPUT, VALUE_DESCID_IN)
        t_port.SetName("t")
        driver_port_out = formula_node.obj.GetOutPort(0)
        for udata, param_name in zip(self.udatas, self.param_names):
            param_port_out = self.object_node.obj.AddPort(c4d.GV_PORT_OUTPUT, udata.desc_id)
            param_ports_out.append(param_port_out)
            param_port_in = formula_node.obj.AddPort(c4d.GV_PORT_INPUT, VALUE_DESCID_IN)
            param_port_in.SetName(param_name)
            param_ports_in.append(param_port_in)
        
        # connect ports
        self.completion_port_out.Connect(t_port)
        driver_port_out.Connect(self.driver_interface_out)
        for param_port_in, param_port_out in zip(param_ports_in, param_ports_out):
            param_port_out.Connect(param_port_in)


class XComposer(XAnimator):
    """special kind of animator used for compositions, uses multiple range mappers instead of formula"""

    def create_mapping(self):
        """not used for composer"""
        pass
        
    def add_range_mapping(self, input_range):
        """adds a range mapper node and an out port to the xpression"""
        # create nodes
        range_mapper_node = XRangeMapper(self.target, input_range=input_range)

        # group nodes
        self.xgroup.add(range_mapper_node)

        # create ports
        self.driver_interface_out = self.obj.AddPort(c4d.GV_PORT_OUTPUT, REAL_DESCID_OUT)

        # connect ports
        range_mapper_node.obj.GetOutPort(0).Connect(self.driver_interface_out)
        self.completion_port_out.Connect(range_mapper_node.obj.GetInPort(0))


class XAccessControl(XPression):
    """xgroup for handling which input should override given parameter"""

    def __init__(self, target, parameter=None, link_target=None, reverse_parameter_range=False):
        # input counter for adding input sources
        self.input_count = 0
        # specify link target
        self.link_target = link_target
        # specify if range mapper should be inserted before parameter
        self.reverse_parameter_range = reverse_parameter_range
        # check for animator
        if type(parameter) in (XAnimator, XComposer):
            animator = parameter  # is animator
            self.parameter = animator.completion_slider
            self.name = animator.name
        elif type(parameter) is UParameter:
            self.parameter = parameter
            self.name = parameter.name
            target = parameter.target
        else:
            raise TypeError("parameter must be of type XAnimator, XComposer or UParameter!")
        super().__init__(target)

    def construct(self):
        # create nodes
        self.condition_switch_node = XConditionSwitch(self.target)
        self.condition_node = XCondition(self.target)
        object_node_out = XObject(self.target, link_target=self.link_target)
        object_node_in = XObject(self.target, link_target=self.link_target)
        nodes = [self.condition_switch_node, self.condition_node, object_node_out, object_node_in]
        if self.reverse_parameter_range:
            self.range_mapper_node_in = XRangeMapper(self.target, reverse=True)
            self.range_mapper_node_out = XRangeMapper(self.target, reverse=True)
            optional_nodes = [self.range_mapper_node_in, self.range_mapper_node_out]
            nodes += optional_nodes

        # group nodes
        self.xgroup = XGroup(*nodes, name=self.name+"AccessControl")
        self.obj = self.xgroup.obj

        # create ports
        self.active_interfaces_in = []
        self.driver_interfaces_in = []
        self.parameter_port_out = object_node_out.obj.AddPort(c4d.GV_PORT_OUTPUT, self.parameter.desc_id)
        self.parameter_port_in = object_node_in.obj.AddPort(c4d.GV_PORT_INPUT, self.parameter.desc_id)

        # connect ports
        self.condition_switch_node.obj.GetOutPort(0).Connect(self.condition_node.obj.GetInPort(0))
        self.parameter_port_out.Connect(self.condition_node.obj.GetInPort(1))
        self.condition_node.obj.GetOutPort(0).Connect(self.parameter_port_in)
        if self.reverse_parameter_range:
            self.range_mapper_node_in.obj.GetOutPort(0).Connect(self.condition_node.obj.GetInPort(1))
            self.range_mapper_node_out.obj.GetOutPort(0).Connect(self.parameter_port_in)
            self.parameter_port_out.Connect(self.range_mapper_node_in.obj.GetInPort(0))
            self.condition_node.obj.GetOutPort(0).Connect(self.range_mapper_node_out.obj.GetInPort(0))

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
        self.active_interfaces_in.append(self.obj.AddPort(c4d.GV_PORT_INPUT, BOOL_DESCID_IN))
        self.driver_interfaces_in.append(self.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN))
        new_condition_switch_port_in = self.condition_switch_node.obj.AddPort(c4d.GV_PORT_INPUT, CONDITION_SWITCH_DESCID_IN)
        new_condition_port_in = self.condition_node.obj.AddPort(c4d.GV_PORT_INPUT, CONDITION_DESCID_IN)

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
            if self.reverse_parameter_range:
                initial_source = self.range_mapper_node_in.obj.GetOutPort(0)
            else:
                initial_source = self.parameter_port_out
            self.interpose_interpolator(source, initial_source, self.driver_interfaces_in[-1], new_condition_port_in)

    def interpose_interpolator(self, source, initial_source, completion_source, output_target):
        """interposes an interpolator for linear interpolation between initial and final value of target parameter"""
        # create nodes
        interpolator = XInterpolator(self.target)

        # group nodes
        self.xgroup.add(interpolator)

        # create ports
        final_source = self.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN)

        # connect ports
        initial_source.Connect(interpolator.ini_interface_in)
        final_source.Connect(interpolator.fin_interface_in)
        source.final_interface_out.Connect(final_source)
        completion_source.Connect(interpolator.completion_interface_in)
        interpolator.output_interface_out.Connect(output_target)


class XComposition(XPression):
    """template for generic composed animator"""

    def __init__(self, *animator_tuples, target=None, name=None):
        self.animator_tuples = animator_tuples
        self.target = target
        self.obj_target = target.obj
        self.name = name
        super().__init__(target)

    def construct(self):
        # unpack tuples
        animators = [animator_tuple[0] for animator_tuple in self.animator_tuples]
        input_ranges = [animator_tuple[1] for animator_tuple in self.animator_tuples]
        # create composer
        composer = XComposer(self.target, name=self.name)
        # create access controls
        for animator, input_range in zip(animators, input_ranges):
            if animator.access_control is None:  # add access control if needed
                animator.access_control = XAccessControl(self.target, parameter=animator)
            composer.add_range_mapping(input_range)
            animator.access_control.add_input_source(composer)


class XAnimation(XPression):
    """connects animators to layer zero parameter"""

    def __init__(self, *animators, target=None, parameter=None, name=None, reverse_parameter_range=False):
        self.target = target
        self.animators = animators
        self.parameter = parameter
        self.obj_target = target.obj
        self.name = name
        self.reverse_parameter_range = reverse_parameter_range
        super().__init__(target)

    def construct(self):
        # create access controls if needed
        for animator in self.animators:
            if self.parameter.access_control is None:
                self.parameter.access_control = XAccessControl(self.target, parameter=self.parameter, link_target=self.parameter.link_target, reverse_parameter_range=self.reverse_parameter_range)
            self.parameter.access_control.add_input_source(animator, interpolate=animator.interpolate)

## OBSOLETE ##

class XMaterialControl(XPression):

    def __init__(self, target):
        self.target = target
        self.obj_target = target.obj
        self.sketch_target = target.sketch_material.obj
        super().__init__(target)

    def construct(self):
        # create nodes
        draw_animator = XAnimator(self.target, name="Draw")
        condition_switch_node = XConditionSwitch(self.target)
        sketch_target_node_in = XObject(self.target, link_target=self.sketch_target)
        sketch_target_node_out = XObject(self.target, link_target=self.sketch_target)
        condition_node = XCondition(self.target)

        # group nodes
        self.xgroup = XGroup(draw_animator, condition_switch_node, sketch_target_node_in,
            sketch_target_node_out, condition_node, name="MaterialControl")
        self.obj = self.xgroup.obj
        
        # gather desc_ids
        sketch_completion_desc_id = c4d.DescID(c4d.DescLevel(
            c4d.OUTLINEMAT_ANIMATE_STROKE_SPEED_COMPLETE, c4d.DTYPE_REAL, 0))
        
        # create ports
        sketch_completion_port_in = sketch_target_node_in.obj.AddPort(
            c4d.GV_PORT_INPUT, sketch_completion_desc_id)
        sketch_completion_port_out = sketch_target_node_out.obj.AddPort(
            c4d.GV_PORT_OUTPUT, sketch_completion_desc_id)
        
        # connect ports
        sketch_completion_port_out.Connect(condition_node.obj.GetInPort(1))
        condition_node.obj.GetOutPort(0).Connect(sketch_completion_port_in)
        condition_switch_node.obj.GetOutPort(0).Connect(condition_node.obj.GetInPort(0))
        draw_animator.driver_interface_out.Connect(condition_node.obj.GetInPort(2))
        draw_animator.active_interface_out.Connect(condition_switch_node.obj.GetInPort(0))

        # remove unused ports
        condition_switch_node.obj.RemoveUnusedPorts()