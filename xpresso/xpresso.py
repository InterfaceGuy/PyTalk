from pydeation.constants import *
import c4d


class XNode:
    """creates a node inside a the xpresso tag of a given target"""

    def __init__(self, target, node_type, parent=None, name=None, custom_tag=False, freeze_tag=False, composition_level=None):
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
            "rangemapper": c4d.ID_OPERATOR_RANGEMAPPER,
            "reals2vec": c4d.ID_OPERATOR_REAL2VECT,
            "vec2reals": c4d.ID_OPERATOR_VECT2REAL
        }
        # set attributes
        self.target = target
        # set xtag to animator tag as default
        self.xtag = target.animator_tag.obj
        if freeze_tag:
            self.xtag = target.freeze_tag.obj
        if composition_level:
            if len(target.composition_tags) < composition_level:
                self.xtag = target.add_composition_tag()
            else:
                self.xtag = target.composition_tags[composition_level - 1].obj
        if custom_tag:
            self.xtag = target.custom_tag.obj
        self.master = self.xtag.GetNodeMaster()
        # get parent xgroup/root
        if parent is None:
            parent = self.master.GetRoot()
        # create node as child of parent
        self.obj = self.master.CreateNode(
            parent, id=node_types[node_type])
        self.name = name
        # set name
        if name is not None:
            self.obj.SetName(name)
        # set optional additional parameters
        self.set_params()

    def __repr__(self):
        return self.__class__.__name__

    def set_params(self):
        """used for setting optional additional parameters"""
        pass


class XGroup(XNode):
    """creates an xgroup containing specified nodes"""

    def __init__(self, *nodes, name=None, inputs_first=False, **kwargs):
        target = nodes[0].target  # rip target from first group member
        self.inputs_first = inputs_first
        super().__init__(target, "group", name=name, **kwargs)  # create group node
        self.add(*nodes)

    def add(self, *nodes):
        """add node to xgroup"""
        for node in nodes:
            # insert node under group
            self.master.InsertFirst(self.obj, node.obj)

    def set_params(self):
        # makes sure inputs are updated before being fed into xgroup
        self.obj[c4d.GV_GROUP_INPUTS_FIRST] = self.inputs_first
        self.obj[c4d.GV_GROUP_ACTIVE] = True


class XObject(XNode):
    """creates an object node"""

    def __init__(self, target, link_target=None, **kwargs):
        self.link_target = link_target
        super().__init__(target, "object", **kwargs)

    def set_params(self):
        if self.link_target is not None:
            self.obj[c4d.GV_OBJECT_OBJECT_ID] = self.link_target.obj


class XCondition(XNode):
    """creates a condition node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "condition", **kwargs)


class XConstant(XNode):
    """creates a constant node"""

    def __init__(self, target, value=0, **kwargs):
        self.value = value
        super().__init__(target, "constant", **kwargs)

    def set_params(self):
        self.obj[c4d.GV_CONST_VALUE] = self.value  # set value


class XCompare(XNode):
    """creates a compare node"""

    def __init__(self, target, mode="==", comparison_value=0, **kwargs):
        self.mode = mode
        self.comparison_value = comparison_value
        super().__init__(target, "compare", **kwargs)

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
        # set comparison value
        self.obj[c4d.GV_CMP_INPUT2] = self.comparison_value


class XBool(XNode):
    """creates a bool node"""

    def __init__(self, target, mode="AND", **kwargs):
        self.mode = mode
        super().__init__(target, "bool", **kwargs)

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

    def __init__(self, target, history_level=1, history_depth=3, **kwargs):
        self.history_level = history_level
        self.history_depth = history_depth
        super().__init__(target, "memory", **kwargs)

    def set_params(self):
        # set history level
        self.obj[c4d.GV_MEMORY_HISTORY_SWITCH] = self.history_level
        # set history depth
        self.obj[c4d.GV_MEMORY_HISTORY_DEPTH] = self.history_depth


class XPython(XNode):
    """creates a python node"""

    def __init__(self, target, name=None, **kwargs):
        super().__init__(target, "python", name=name, **kwargs)


class XConditionSwitch(XPython):

    def __init__(self, target, name="ConditionSwitch", **kwargs):
        super().__init__(target, name=name, **kwargs)

    def set_params(self):
        self.obj[c4d.GV_PYTHON_CODE] = 'import c4d\n\ndef main():\n    global Output1\n    Output1 = 0\n    for i in range(op.GetInPortCount()):\n        port = op.GetInPort(i)\n        value = globals()[port.GetName(op)]\n        if value == 1:\n            Output1 = i+1\n            return'


class XDelta(XPython):
    """outputs delta of input values if delta != 0 else outputs 1"""

    def __init__(self, target, name="Delta", **kwargs):
        super().__init__(target, name=name, **kwargs)

    def set_params(self):
        self.obj[c4d.GV_PYTHON_CODE] = 'import c4d\n\ndef main():\n    global Output1\n    Output1 = 1\n    delta_t = Input1 - Input2\n    if delta_t:\n        Output1 = delta_t'


class XFormula(XNode):
    """creates a formula node"""

    def __init__(self, target, variables=["t"], formula="t", **kwargs):
        self.variables = variables
        self.formula = "t"
        if formula:
            self.formula = formula
        super().__init__(target, "formula", **kwargs)

    def set_params(self):
        # add variables
        self.variable_ports = {}
        for variable_name in self.variables:
            variable_port = self.obj.AddPort(
                c4d.GV_PORT_INPUT, VALUE_DESCID_IN)
            variable_port.SetName(variable_name)
            self.variable_ports[variable_name] = variable_port
        # set formula
        self.obj[c4d.GV_FORMULA_STRING] = self.formula
        # set options
        self.obj[c4d.GV_FORMULA_USE_PORTNAMES] = True  # use portnames
        self.obj[c4d.GV_FORMULA_ANGLE] = 1  # use radians


class XRangeMapper(XNode):
    """creates a range mapper node"""

    def __init__(self, target, input_range=(0, 1), easing=False, reverse=False, **kwargs):
        self.input_range = input_range
        self.easing = easing
        self.reverse = reverse
        super().__init__(target, "rangemapper", **kwargs)

    def set_params(self):
        # create spline
        spline = c4d.SplineData()
        spline.MakeLinearSplineBezier()
        # set easing
        knot_ini, knot_fin = spline.GetKnots()
        if self.easing is True:
            spline.SetKnot(0, knot_ini["vPos"], knot_ini["lFlagsSettings"], vTangentLeft=c4d.Vector(
                0, 0, 0), vTangentRight=c4d.Vector(0.25, 0, 0))
            spline.SetKnot(1, knot_fin["vPos"], knot_fin["lFlagsSettings"],
                           vTangentLeft=c4d.Vector(-0.25, 0, 0), vTangentRight=c4d.Vector(0, 0, 0))
        elif self.easing == "IN":
            spline.SetKnot(0, knot_ini["vPos"], knot_ini["lFlagsSettings"], vTangentLeft=c4d.Vector(
                0, 0, 0), vTangentRight=c4d.Vector(0.25, 0, 0))
        elif self.easing == "OUT":
            spline.SetKnot(1, knot_fin["vPos"], knot_fin["lFlagsSettings"],
                           vTangentLeft=c4d.Vector(-0.25, 0, 0), vTangentRight=c4d.Vector(0, 0, 0))

        self.obj[c4d.GV_RANGEMAPPER_SPLINE] = spline
        # set options
        # set output range to zero to one
        self.obj[c4d.GV_RANGEMAPPER_OUTPUT_DEFS] = 4
        self.obj[c4d.GV_RANGEMAPPER_CLAMP_LOWER] = True
        self.obj[c4d.GV_RANGEMAPPER_CLAMP_UPPER] = True
        self.obj[c4d.GV_RANGEMAPPER_REVERSE] = self.reverse
        # set range
        self.obj[c4d.GV_RANGEMAPPER_RANGE11] = self.input_range[0]
        self.obj[c4d.GV_RANGEMAPPER_RANGE12] = self.input_range[1]


class XFreeze(XNode):
    """creates a freeze node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "freeze", **kwargs)


class XVec2Reals(XNode):
    """creates a vec2reals node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "vec2reals", **kwargs)


class XReals2Vec(XNode):
    """creates a reals2vec node"""

    def __init__(self, target, **kwargs):
        super().__init__(target, "reals2vec", **kwargs)


class XMath(XNode):
    """creates a math node"""

    def __init__(self, target, mode="+", **kwargs):
        self.mode = mode
        super().__init__(target, "math", **kwargs)

    def set_params(self):
        # define modes
        modes = {
            "+": 0,
            "-": 1,
            "*": 2,
            "/": 3,
            "%": 4
        }
        # specify mode
        self.obj[c4d.GV_MATH_FUNCTION_ID] = modes[self.mode]
