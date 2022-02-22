from pydeation.objects.abstract_objects import HelperObject
import c4d

class Null(HelperObject):

    def __init__(self, display="dot", **kwargs):
        super().__init__(**kwargs)
        self.set_object_properties(display=display)

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Onull)

    def set_object_properties(self, display="dot"):
        # implicit properties
        shapes = {"dot": 0, "cross": 1, "circle": 2, None: 14}
        # set properties
        self.obj[c4d.NULLOBJECT_DISPLAY] = shapes[display]

class Group(Null):

    def __init__(self, *children, **kwargs):
        super().__init__(**kwargs)
        self.children = list(children)
        self.add_children()

    def __iter__(self):
        self.idx = 0
        return self

    def __next__(self):
        if self.idx < len(self.children):
            child = self.children[self.idx]
            self.idx += 1
            return child
        else:
            raise StopIteration

    def __getitem__(self, index):
        return self.children[index]

    def add_children(self):
        for child in self.children[::-1]:
            child.obj.InsertUnder(self.obj)

    def add(self, *children):
        for child in children:
            self.children.append(child)
            child.obj.InsertUnder(self.obj)
