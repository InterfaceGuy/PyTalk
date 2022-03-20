from abc import ABC, abstractmethod
import c4d


class UData(ABC):
    """creates userdata for xpresso setups"""

    def __init__(self, name=None):
        # create default container for the specified data type
        self.specify_data_type()
        # set constraints
        self.specify_constraints()
        # set the display name of the element
        self.specify_name(name)
        # add attribute for descId
        self.descId = None

    @abstractmethod
    def specify_data_type():
        pass

    def specify_name(self, name):
        # sets the display name of the element
        self.name = name  # write as attribute
        self.bc[c4d.DESC_NAME] = name


### data type classes ###

class UGroup(UData):
    """creates a user data group element"""

    def __init__(self, *children, target=None, **kwargs):

        super().__init__(**kwargs)

        self.descId = target.AddUserData(self.bc)

        for child in children:
            # add as child
            child.bc[c4d.DESC_PARENTGROUP] = self.descId
            # Add the user data element, retrieving its DescId.
            child.descId = target.AddUserData(child.bc)

    def specify_data_type(self):
        # create base container
        self.bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_GROUP)

    def specify_constraints(self):
        pass


class UReal(UData):
    """creates a field of type real"""

    def specify_data_type(self):
        # create base container
        self.bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)

    @abstractmethod
    def specify_constraints():
        pass


class UInt(UData):
    """creates an integer field"""

    def specify_data_type(self):
        # create base container
        self.bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_LONG)

    @abstractmethod
    def specify_constraints():
        pass


class UBool(UData):
    """creates a bool field"""

    def specify_data_type(self):
        # create base container
        self.bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BOOL)

    @abstractmethod
    def specify_constraints():
        pass


### concrete classes ###

class UCompletion(UReal):
    """creates a completion field: t -> [0,1]"""

    def specify_constraints(self):
        # set range
        self.bc[c4d.DESC_MIN] = 0
        self.bc[c4d.DESC_MAX] = 1
        # set unit to percent
        self.bc[c4d.DESC_UNIT] = c4d.DESC_UNIT_PERCENT
        # set step size to one percent
        self.bc[c4d.DESC_STEP] = 0.01
        # set interface to slider
        self.bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_REALSLIDER

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "completion"
        super().specify_name(name)


class UAngle(UReal):
    """creates an angle field: phi -> [0,2π]"""

    def specify_constraints(self):
        # set range
        self.bc[c4d.DESC_MIN] = 0
        self.bc[c4d.DESC_MAX] = 2 * PI

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "angle"
        super().specify_name(name)


class UStrength(UReal):
    """creates a strength field: s -> [0,∞)"""

    def specify_constraints(self):
        # set lower bound
        self.bc[c4d.DESC_MIN] = 0

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "strength"
        super().specify_name(name)


class UCount(UInt):
    """creates a positive number field: n -> N"""

    def specify_constraints(self):
        # set lower bound
        self.bc[c4d.DESC_MIN] = 0

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "count"
        super().specify_name(name)


class UCheckBox(UBool):
    """creates a check box field: b -> {0,1}"""

    def specify_name(self, name):
        # sets the display name of the element
        if name is None:
            name = "checkbox"
        super().specify_name(name)
