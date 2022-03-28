from abc import ABC, abstractmethod
import c4d

# missing desc_ids
VALUE_DESCID_IN = c4d.DescID(c4d.DescLevel(2000, 400007003, 400001133))

class XNode:
    """creates a node inside a the xpresso tag of a given target"""

    def __init__(self, target, node_type, parent=None, name=None):
        node_types = {
            "group": c4d.ID_GV_OPERATOR_GROUP,
            "bool": c4d.ID_OPERATOR_BOOL,
            "compare": c4d.ID_OPERATOR_CMP,
            "condition": c4d.ID_OPERATOR_CONDITION,
            "constant": c4d.ID_OPERATOR_CONST,
            "formula": c4d.ID_OPERATOR_FORMULA,
            "freeze": c4d.ID_OPERATOR_FREEZE,
            "math": c4d.ID_OPERATOR_MATH,
            "matrix2vect": c4d.ID_OPERATOR_MATRIX2VECT,
            "memory": c4d.ID_OPERATOR_MEMORY,
            "object": c4d.ID_OPERATOR_OBJECT,
            "python": 1022471,
            "rangemapper": c4d.ID_OPERATOR_RANGEMAPPER
        }

        self.target = target
        self.xtag = target.xtag.obj
        self.master = self.xtag.GetNodeMaster()
        if parent is None:
            parent = self.master.GetRoot()
        self.obj = self.master.CreateNode(
            parent, id=node_types[node_type])  # create node
        self.name = name
        if name is not None:
            self.obj.SetName(name)  # set name
        self.set_params()  # set optional additional parameters

    def set_params(self):
        """used for setting optional additional parameters"""
        pass


class XGroup(XNode):
    """creates an xgroup containing specified nodes"""

    def __init__(self, *nodes, name=None):
        target = nodes[0].target  # rip target from first group member
        super().__init__(target, "group", name=name)  # create group node
        self.add(*nodes)

    def add(self, *nodes):
        """add node to xgroup"""
        for node in nodes:
            # insert node under group
            self.master.InsertFirst(self.obj, node.obj)



class XObject(XNode):
    """creates an object node"""

    def __init__(self, target, link_target=None):
        self.link_target = link_target
        super().__init__(target, "object")

    def set_params(self):
        if self.link_target is not None:
            self.obj[c4d.GV_OBJECT_OBJECT_ID] = self.link_target.obj


class XCondition(XNode):
    """creates a condition node"""

    def __init__(self, target):
        super().__init__(target, "condition")


class XConstant(XNode):
    """creates a constant node"""

    def __init__(self, target, value=0):
        self.value = value
        super().__init__(target, "constant")

    def set_params(self):
        self.obj[c4d.GV_CONST_VALUE] = self.value  # set value


class XCompare(XNode):
    """creates a compare node"""

    def __init__(self, target, mode="==", comparison_value=0):
        self.mode = mode
        self.comparison_value = comparison_value
        super().__init__(target, "compare")

    def set_params(self):
        modes = {
            "==": 0,
            "<": 1,
            "<=": 2,
            ">": 3,
            ">=": 4,
            "!=": 5,
        }
        self.obj[c4d.GV_CMP_FUNCTION] = modes[self.mode]  # set mode
        self.obj[c4d.GV_CMP_INPUT2] = self.comparison_value  # set comparison value

class XBool(XNode):
    """creates a bool node"""

    def __init__(self, target, mode="AND"):
        self.mode = mode
        super().__init__(target, "bool")

    def set_params(self):
        modes = {
            "AND": 0,
            "OR": 1,
            "XOR": 2,
            "NAND": 3,
            "NOR": 4,
            "NXOR": 5,
        }
        self.obj[c4d.GV_BOOL_FUNCTION_ID] = modes[self.mode]  # set mode


class XMemory(XNode):
    """creates a memory node"""

    def __init__(self, target, history_level=1, history_depth=3):
        self.history_level = history_level
        self.history_depth = history_depth
        super().__init__(target, "memory")

    def set_params(self):
        self.obj[c4d.GV_MEMORY_HISTORY_SWITCH] = self.history_level  # set history level
        self.obj[c4d.GV_MEMORY_HISTORY_DEPTH] = self.history_depth  # set history depth


class XPython(XNode):
    """creates a python node"""

    def __init__(self, target, name=None):
        super().__init__(target, "python", name=name)


class XConditionSwitch(XPython):

    def __init__(self, target, name="ConditionSwitch"):
        super().__init__(target, name=name)

    def set_params(self):
        self.obj[c4d.GV_PYTHON_CODE] = 'import c4d\n\ndef main():\n    global Output1\n    Output1 = 0\n    for i in range(op.GetInPortCount()):\n        port = op.GetInPort(i)\n        value = globals()[port.GetName(op)]\n        if value == 1:\n            Output1 = i+1\n            return'


class XFormula(XNode):
    """creates a formula node"""

    def __init__(self, target, variables=[], formula=None):
        self.variables = variables
        self.formula = formula
        super().__init__(target, "formula")

    def set_params(self):
        # add variables
        for variable in self.variables:
            variable_port = self.obj.AddPort(c4d.GV_PORT_INPUT, VALUE_DESCID_IN)
            variable_port.SetName(variable)
        # set formula
        if self.formula is None:
            self.formula = "t"
        self.obj[c4d.GV_FORMULA_STRING] = self.formula
        # set options
        self.obj[c4d.GV_FORMULA_USE_PORTNAMES] = True  # use portnames
        self.obj[c4d.GV_FORMULA_ANGLE] = 1  # use radians


class XRangeMapper(XNode):
    """creates a range mapper node"""

    def __init__(self, target, input_range=(0,1), easing=False, reverse=False):
        self.input_range = input_range
        self.easing = easing
        self.reverse = reverse
        super().__init__(target, "rangemapper")

    def set_params(self):
        # create spline
        spline = c4d.SplineData()
        spline.MakeLinearSplineBezier()
        # set easing
        knot_ini, knot_fin = spline.GetKnots()
        if self.easing is True:
            spline.SetKnot(0, knot_ini["vPos"], knot_ini["lFlagsSettings"], vTangentLeft=c4d.Vector(0,0,0), vTangentRight=c4d.Vector(0.25,0,0))
            spline.SetKnot(1, knot_fin["vPos"], knot_fin["lFlagsSettings"], vTangentLeft=c4d.Vector(-0.25,0,0), vTangentRight=c4d.Vector(0,0,0))
        elif self.easing == "IN":
            spline.SetKnot(0, knot_ini["vPos"], knot_ini["lFlagsSettings"], vTangentLeft=c4d.Vector(0,0,0), vTangentRight=c4d.Vector(0.25,0,0))
        elif self.easing == "OUT":
            spline.SetKnot(1, knot_fin["vPos"], knot_fin["lFlagsSettings"], vTangentLeft=c4d.Vector(-0.25,0,0), vTangentRight=c4d.Vector(0,0,0))

        self.obj[c4d.GV_RANGEMAPPER_SPLINE] = spline
        # set options
        self.obj[c4d.GV_RANGEMAPPER_OUTPUT_DEFS] = 4  # set output range to zero to one
        self.obj[c4d.GV_RANGEMAPPER_CLAMP_LOWER] = True
        self.obj[c4d.GV_RANGEMAPPER_CLAMP_UPPER] = True
        self.obj[c4d.GV_RANGEMAPPER_REVERSE] = self.reverse
        # set range
        self.obj[c4d.GV_RANGEMAPPER_RANGE11] = self.input_range[0]
        self.obj[c4d.GV_RANGEMAPPER_RANGE12] = self.input_range[1]


class XFreeze(XNode):
    """creates a freeze node"""

    def __init__(self, target):
        super().__init__(target, "freeze")


class XPression(ABC):
    """creates xpressions for a given xpresso tag"""

    def __init__(self, target):
        self.target = target
        self.construct()

    @abstractmethod
    def construct():
        """analogous to scene class this function constructs the xpression"""
        pass