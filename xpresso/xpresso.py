from abc import ABC, abstractmethod
import c4d


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


class XGroup(XNode):
    """creates an xgroup containing specified nodes"""

    def __init__(self, *nodes, name=None):
        target = nodes[0].target  # rip target from first group member
        super().__init__(target, "group", name=name)  # create group node
        for node in nodes:
            # insert node under group
            self.master.InsertFirst(self.obj, node.obj)


class XObject(XNode):
    """creates an object node"""

    def __init__(self, target, obj_target=None):
        super().__init__(target, "object")


class XCondition(XNode):
    """creates a condition node"""

    def __init__(self, target):
        super().__init__(target, "condition")


class XCompare(XNode):
    """creates a compare node"""

    def __init__(self, target):
        super().__init__(target, "compare")


class XBool(XNode):
    """creates a bool node"""

    def __init__(self, target):
        super().__init__(target, "bool")


class XMemory(XNode):
    """creates a memory node"""

    def __init__(self, target):
        super().__init__(target, "memory")

class XPython(XNode):
    """creates a python node"""

    def __init__(self, target):
        super().__init__(target, "python")

class XFormula(XNode):
    """creates a formula node"""

    def __init__(self, target, formula=None):
        super().__init__(target, "formula")

class XPression(ABC):
    """creates xpressions for a given xpresso tag"""

    def __init__(self, target):
        self.target = target
        self.xtag = target.xtag.obj  # xpresso tag
        self.master = self.xtag.GetNodeMaster()
        self.construct()

    @abstractmethod
    def construct():
        """analogous to scene class this function constructs the xpression"""
        pass