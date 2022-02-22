from abc import ABC, abstractmethod
import c4d


class XNode:
    """creates a node inside a given xpresso tag"""

    def __init__(self, master, node_type, parent=None, name=None):
        node_types = {
            "group": c4d.ID_GV_OPERATOR_GROUP,
            "bool": c4d.ID_OPERATOR_BOOL,
            "condition": c4d.ID_OPERATOR_CONDITION,
            "constant": c4d.ID_OPERATOR_CONST,
            "formula": c4d.ID_OPERATOR_FORMULA,
            "freeze": c4d.ID_OPERATOR_FREEZE,
            "math": c4d.ID_OPERATOR_MATH,
            "matrix2vect": c4d.ID_OPERATOR_MATRIX2VECT,
            "memory": c4d.ID_OPERATOR_MEMORY,
            "object": c4d.ID_OPERATOR_OBJECT,
            "rangemapper": c4d.ID_OPERATOR_RANGEMAPPER
        }

        self.master = master
        if parent is None:
            parent = self.master.GetRoot()
        self.obj = master.CreateNode(
            parent, id=node_types[node_type])  # create node


class XObject(XNode):
    """creates an object node"""

    def __init__(self, master):
        super().__init__(master, "object")


class XGroup(XNode):
    """creates an xgroup containing specified nodes"""

    def __init__(self, *nodes, master=None, name=None):
        super().__init__(master, "group", name=name)  # create group node
        for node in nodes:
            # insert node under group
            self.master.InsertFirst(self.obj, node.obj)


class XPression(ABC):
    """creates xpressions for a given xpresso tag"""

    def __init__(self, xtag):
        self.xtag = xtag  # xpresso tag
        self.master = self.xtag.GetNodeMaster()

    @abstractmethod
    def construct(self):
        """analogous to scene class this function constructs the xpression"""
        pass


class MaterialControl(XPression):
    """creates the material control xpression necessary for every visible object"""
