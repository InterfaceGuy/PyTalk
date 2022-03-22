from pydeation.xpresso.xpresso import *
from pydeation.xpresso.userdata import *
import c4d

# missing descIds
REAL_DESCID_IN = c4d.DescID(c4d.DescLevel(1000019, 400007003, 1001144))
REAL_DESCID_OUT = c4d.DescID(c4d.DescLevel(536870931, 400007003, 1001144))
BOOL_DESCID_IN = c4d.DescID(c4d.DescLevel(401006001, 400007001, 1001144))
BOOL_DESCID_OUT = c4d.DescID(c4d.DescLevel(936876913, 400007001, 1001144))
INTEGER_DESCID_IN = c4d.DescID(c4d.DescLevel(1000015, 400007002, 1001144))
INTEGER_DESCID_OUT = c4d.DescID(c4d.DescLevel(536870927, 400007002, 1001144))
VALUE_DESCID_IN = c4d.DescID(c4d.DescLevel(2000, 400007003, 400001133))
CONDITION_DESCID_IN = c4d.DescID(c4d.DescLevel(2000, 400007003, 400001117))
CONDITION_SWITCH_DESCID_IN = c4d.DescID(c4d.DescLevel(4005, 400007003, 1022471))


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
        memory_node = XMemory(self.target, history_level=1)
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
        not_descending_node = XNotDescending(self.target)
        bool_node = XBool(self.target, mode="AND")

        # group nodes
        self.xgroup = XGroup(active_range_node, not_descending_node, bool_node, name="OverrideController")
        self.obj = self.xgroup.obj

        # create ports
        self.real_interface_in = self.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.bool_interface_out = self.obj.AddPort(c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)

        # connect ports
        self.real_interface_in.Connect(active_range_node.real_interface_in)
        self.real_interface_in.Connect(not_descending_node.real_interface_in)
        active_range_node.bool_interface_out.Connect(bool_node.obj.GetInPort(0))
        not_descending_node.bool_interface_out.Connect(bool_node.obj.GetInPort(1))
        bool_node.obj.GetOutPort(0).Connect(self.bool_interface_out)


class XAnimator(XPression):
    """template for generic animator that drives single parameter using a given formula"""

    def __init__(self, target, formula=None, name=None, params=[]):
        self.target = target
        self.obj_target = target.obj
        self.formula = formula
        self.name = name
        self.params = params
        self.access_control = None
        super().__init__(target)
        self.create_mapping()  # creates the mapping

    def construct(self):
        # create userdata
        self.completion_slider = UCompletion()
        for i, udata in enumerate(self.params):
            self.params[i] = udata()
        u_group = UGroup(self.completion_slider, *self.params, target=self.obj_target, name=self.name)

        # create nodes
        self.object_node = XObject(self.target)
        override_controller = XOverrideController(self.target)
        
        # group nodes
        self.xgroup = XGroup(self.object_node, override_controller, name=self.name+"Animator")
        self.obj = self.xgroup.obj

        # create ports
        self.active_interface_out = self.obj.AddPort(c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)
        self.completion_port_out = self.object_node.obj.AddPort(c4d.GV_PORT_OUTPUT, self.completion_slider.descId)

        # connect ports
        self.completion_port_out.Connect(override_controller.real_interface_in)
        override_controller.bool_interface_out.Connect(self.active_interface_out)

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
        for i, param in enumerate(self.params):
            param_port_out = self.object_node.obj.AddPort(c4d.GV_PORT_OUTPUT, param.descId)
            param_ports_out.append(param_port_out)
            param_port_in = formula_node.obj.AddPort(c4d.GV_PORT_INPUT, VALUE_DESCID_IN)
            param_port_in.SetName("var"+str(i+1))
            param_ports_in.append(param_port_in)
        
        # connect ports
        self.completion_port_out.Connect(t_port)
        driver_port_out.Connect(self.driver_interface_out)
        for param_port_in, param_port_out in zip(param_ports_in, param_ports_out):
            param_port_out.Connect(param_port_in)


class XComposer(XAnimator):
    """special kind of animator used for compositions, uses multiple range mappers instead of formula"""

    def __init__(self, target, input_range=(0,1), name=None):
        self.input_range = input_range
        super().__init__(target, name=name)

    def create_mapping(self):
        """creates a mapping using range mapper nodes"""
        # create nodes
        range_mapper_node = XRangeMapper(self.target, input_range=self.input_range, easing="OUT")

        # group nodes
        self.xgroup.add(range_mapper_node)

        # create ports
        self.driver_interface_out = self.obj.AddPort(c4d.GV_PORT_OUTPUT, REAL_DESCID_OUT)

        # connect ports
        range_mapper_node.obj.GetOutPort(0).Connect(self.driver_interface_out)
        self.completion_port_out.Connect(range_mapper_node.obj.GetInPort(0))


class XAccessControl(XPression):
    """xgroup for handling which input should override given parameter"""

    def __init__(self, target, parameter=None, link_target=None):
        # input counter for adding input sources
        self.input_count = 0
        # specify link target
        self.link_target = link_target
        # check for animator
        if type(parameter) is XAnimator:
            animator = parameter  # is animator
            self.parameter = animator.completion_slider
            self.name = animator.name
        else:
            self.parameter = parameter
            self.name = parameter.name
        super().__init__(target)

    def construct(self):
        # create nodes
        self.condition_switch_node = XConditionSwitch(self.target)
        self.condition_node = XCondition(self.target)
        object_node_out = XObject(self.target, link_target=self.link_target)
        object_node_in = XObject(self.target, link_target=self.link_target)

        # group nodes
        self.xgroup = XGroup(self.condition_switch_node, self.condition_node, object_node_out, object_node_in, name=self.name+"AccessControl")
        self.obj = self.xgroup.obj

        # create ports
        self.active_interfaces_in = []
        self.driver_interfaces_in = []
        parameter_port_out = object_node_out.obj.AddPort(c4d.GV_PORT_OUTPUT, self.parameter.descId)
        parameter_port_in = object_node_in.obj.AddPort(c4d.GV_PORT_INPUT, self.parameter.descId)

        # connect ports
        self.condition_switch_node.obj.GetOutPort(0).Connect(self.condition_node.obj.GetInPort(0))
        parameter_port_out.Connect(self.condition_node.obj.GetInPort(1))
        self.condition_node.obj.GetOutPort(0).Connect(parameter_port_in)

        # remove unused ports
        self.condition_switch_node.obj.RemoveUnusedPorts()
        self.condition_node.obj.RemoveUnusedPorts()

        # name ports
        self.condition_node.obj.GetInPort(1).SetName("Idle")


    def add_input_source(self, source):
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


class XComposition(XPression):
    """template for generic composed animator"""

    def __init__(self, *sub_animators, target=None, name=None):
        self.sub_animators = sub_animators
        self.target = target
        self.obj_target = target.obj
        self.name = name
        super().__init__(target)

    def construct(self):
        # create nodes
        self.composer = XComposer(self.target, name=self.name)
        self.access_controls = []
        for sub_animator in self.sub_animators:
            access_control = XAccessControl(self.target, parameter=sub_animator.completion_slider)
            access_control.add_input_source(self.composer)
            self.access_controls.append(access_control)
            if sub_animator.access_control is None:  # add access control if needed
                sub_animator.access_control = XAccessControl(self.target, parameter=sub_animator)
            sub_animator.access_control.add_input_source(self.composition_animator)
            self.access_controls.append(sub_animator.access_control)


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
        
        # gather descIds
        sketch_completion_descId = c4d.DescID(c4d.DescLevel(
            c4d.OUTLINEMAT_ANIMATE_STROKE_SPEED_COMPLETE, c4d.DTYPE_REAL, 0))
        
        # create ports
        sketch_completion_port_in = sketch_target_node_in.obj.AddPort(
            c4d.GV_PORT_INPUT, sketch_completion_descId)
        sketch_completion_port_out = sketch_target_node_out.obj.AddPort(
            c4d.GV_PORT_OUTPUT, sketch_completion_descId)
        
        # connect ports
        sketch_completion_port_out.Connect(condition_node.obj.GetInPort(1))
        condition_node.obj.GetOutPort(0).Connect(sketch_completion_port_in)
        condition_switch_node.obj.GetOutPort(0).Connect(condition_node.obj.GetInPort(0))
        draw_animator.driver_interface_out.Connect(condition_node.obj.GetInPort(2))
        draw_animator.active_interface_out.Connect(condition_switch_node.obj.GetInPort(0))

        # remove unused ports
        condition_switch_node.obj.RemoveUnusedPorts()