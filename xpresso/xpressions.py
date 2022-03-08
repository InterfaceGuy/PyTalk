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


class XActiveRange(XPression):
    """xpression for checking if completion is in active range"""

    def construct(self):
        # create nodes
        compare_node_0 = XCompare(self.target)
        compare_node_1 = XCompare(self.target)
        bool_node = XBool(self.target)

        # set params
        compare_node_0.obj[c4d.GV_CMP_FUNCTION] = 5  # !=
        compare_node_1.obj[c4d.GV_CMP_FUNCTION] = 5  # !=
        compare_node_0.obj[c4d.GV_CMP_INPUT2] = 0  # comparison value
        compare_node_1.obj[c4d.GV_CMP_INPUT2] = 1  # comparison value
        
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
        compare_node = XCompare(self.target)

        # group nodes
        self.xgroup = XGroup(memory_node, compare_node, name="NotDescending")
        self.obj = self.xgroup.obj

        # set params
        memory_node.obj[c4d.GV_MEMORY_HISTORY_SWITCH] = 1  # store last frame in memory
        compare_node.obj[c4d.GV_CMP_FUNCTION] = 4  # >=

        # create ports
        self.real_interface_in = self.xgroup.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.bool_interface_out = self.xgroup.obj.AddPort(c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)

        # connect ports
        self.real_interface_in.Connect(memory_node.obj.GetInPort(1))
        self.real_interface_in.Connect(compare_node.obj.GetInPort(0))
        memory_node.obj.GetOutPort(0).Connect(compare_node.obj.GetInPort(1))
        compare_node.obj.GetOutPort(0).Connect(self.bool_interface_out)


class XOverrideController(XPression):
    """xgroup for checking if parameter should be overridden"""

    def construct(self):
        # create nodes
        active_range_node = XActiveRange(self.target)
        not_descending_node = XNotDescending(self.target)
        bool_node = XBool(self.target)

        # group nodes
        self.xgroup = XGroup(active_range_node, not_descending_node, bool_node, name="OverrideController")
        self.obj = self.xgroup.obj

        # set params
        bool_node.obj[c4d.GV_BOOL_FUNCTION_ID] = 0  # AND

        # create ports
        self.real_interface_in = self.xgroup.obj.AddPort(c4d.GV_PORT_INPUT, REAL_DESCID_IN)
        self.bool_interface_out = self.xgroup.obj.AddPort(c4d.GV_PORT_OUTPUT, BOOL_DESCID_OUT)

        # connect ports
        self.real_interface_in.Connect(active_range_node.real_interface_in)
        self.real_interface_in.Connect(not_descending_node.real_interface_in)
        active_range_node.bool_interface_out.Connect(bool_node.obj.GetInPort(0))
        not_descending_node.bool_interface_out.Connect(bool_node.obj.GetInPort(1))
        bool_node.obj.GetOutPort(0).Connect(self.bool_interface_out)


class XMaterialControl(XPression):

    def __init__(self, target):
        self.target = target
        self.obj_target = target.obj
        self.sketch_target = target.sketch_material.obj
        super().__init__(target)

    def construct(self):
        # create userdata
        draw_completion = UCompletion()
        draw_group = UGroup(
            draw_completion, target=self.obj_target, name="Draw")
        
        # create nodes
        override_controller = XOverrideController(self.target)
        obj_target_node = XObject(self.target, obj_target=self.obj_target)
        sketch_target_node_in = XObject(
            self.target, obj_target=self.sketch_target)
        sketch_target_node_out = XObject(
            self.target, obj_target=self.sketch_target)
        condition_node = XCondition(self.target)

        # group nodes
        self.xgroup = XGroup(override_controller, obj_target_node,
            sketch_target_node_in, sketch_target_node_out, condition_node, name="MaterialControl")
        self.obj = self.xgroup.obj
        
        # gather descIds
        sketch_completion_descId = c4d.DescID(c4d.DescLevel(
            c4d.OUTLINEMAT_ANIMATE_STROKE_SPEED_COMPLETE, c4d.DTYPE_REAL, 0))
        
        # create ports
        draw_completion_port = obj_target_node.obj.AddPort(
            c4d.GV_PORT_OUTPUT, draw_completion.descId)
        sketch_completion_port_in = sketch_target_node_in.obj.AddPort(
            c4d.GV_PORT_INPUT, sketch_completion_descId)
        sketch_completion_port_out = sketch_target_node_out.obj.AddPort(
            c4d.GV_PORT_OUTPUT, sketch_completion_descId)
        
        # connect ports
        condition_ports_in = condition_node.obj.GetInPorts()
        condition_port_out = condition_node.obj.GetOutPort(0)
        draw_completion_port.Connect(condition_ports_in[1])
        sketch_completion_port_out.Connect(condition_ports_in[2])
        condition_port_out.Connect(sketch_completion_port_in)
        override_controller.bool_interface_out.Connect(condition_ports_in[0])
        override_controller.real_interface_in.Connect(draw_completion_port)