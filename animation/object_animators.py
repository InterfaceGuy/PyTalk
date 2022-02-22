from pydeation.animation.abstract_animators import ObjectAnimator
import c4d


class SetVisibility(ObjectAnimator):
    """animates the visibility of objects using a state animation"""

    def __new__(cls, *objs, visible=None, **kwargs):
        cls.set_values(visible)
        return super().__new__(cls, *objs, animation_type="state", **kwargs)

    @classmethod
    def specify_desc_ids(cls):
        cls.desc_ids = {
            "vis_editor": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_VISIBILITY_EDITOR, c4d.DTYPE_LONG, 0)),
            "vis_render": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_VISIBILITY_RENDER, c4d.DTYPE_LONG, 0))
        }

    @classmethod
    def set_values(cls, visible):
        # translate to c4d values
        if visible:
            visibility = 0
        else:
            visibility = 1
        # equate render and editor visibility
        visibility_editor = visibility_render = visibility
        cls.values = [visibility_editor, visibility_render]


class Show(SetVisibility):
    """enables the visibility of objects"""

    def __new__(cls, *objs, **kwargs):
        return super().__new__(cls, *objs, visible=True, **kwargs)


class Hide(SetVisibility):
    """disables the visiblity of objects"""

    def __new__(cls, *objs, **kwargs):
        return super().__new__(cls, *objs, visible=False, **kwargs)


class Move(ObjectAnimator):
    """animates the position of objects"""

    def __new__(cls, *objs, x=None, y=None, z=None, relative=True, **kwargs):
        cls.set_values(x, y, z)
        return super().__new__(cls, *objs, relative=relative, **kwargs)

    @classmethod
    def specify_desc_ids(cls):
        cls.desc_ids = {
            "pos_x": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_POSITION, c4d.DTYPE_VECTOR, 0),
                                c4d.DescLevel(c4d.VECTOR_X, c4d.DTYPE_REAL, 0)),
            "pos_y": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_POSITION, c4d.DTYPE_VECTOR, 0),
                                c4d.DescLevel(c4d.VECTOR_Y, c4d.DTYPE_REAL, 0)),
            "pos_z": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_POSITION, c4d.DTYPE_VECTOR, 0),
                                c4d.DescLevel(c4d.VECTOR_Z, c4d.DTYPE_REAL, 0))
        }

    @classmethod
    def set_values(cls, x, y, z):
        cls.values = [x, y, z]


class Rotate(ObjectAnimator):
    """animates the rotation of objects"""

    def __new__(cls, *objs, h=None, p=None, b=None, relative=True, **kwargs):
        cls.set_values(h, p, b)
        return super().__new__(cls, *objs, relative=relative, **kwargs)

    @classmethod
    def specify_desc_ids(cls):
        cls.desc_ids = {
            "rot_h": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_ROTATION, c4d.DTYPE_VECTOR, 0),
                                c4d.DescLevel(c4d.VECTOR_X, c4d.DTYPE_REAL, 0)),
            "rot_p": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_ROTATION, c4d.DTYPE_VECTOR, 0),
                                c4d.DescLevel(c4d.VECTOR_Y, c4d.DTYPE_REAL, 0)),
            "rot_b": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_ROTATION, c4d.DTYPE_VECTOR, 0),
                                c4d.DescLevel(c4d.VECTOR_Z, c4d.DTYPE_REAL, 0))
        }

    @classmethod
    def set_values(cls, h, p, b):
        cls.values = [h, p, b]


class Scale(ObjectAnimator):
    """animates the scale of objects"""

    def __new__(cls, *objs, x=None, y=None, z=None, relative=True, multiplicative=True, **kwargs):
        cls.set_values(x, y, z)
        return super().__new__(cls, *objs, relative=relative, multiplicative=multiplicative, **kwargs)

    @classmethod
    def specify_desc_ids(cls):
        cls.desc_ids = {
            "scale_x": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_SCALE, c4d.DTYPE_VECTOR, 0),
                                  c4d.DescLevel(c4d.VECTOR_X, c4d.DTYPE_REAL, 0)),
            "scale_y": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_SCALE, c4d.DTYPE_VECTOR, 0),
                                  c4d.DescLevel(c4d.VECTOR_Y, c4d.DTYPE_REAL, 0)),
            "scale_z": c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_SCALE, c4d.DTYPE_VECTOR, 0),
                                  c4d.DescLevel(c4d.VECTOR_Z, c4d.DTYPE_REAL, 0))
        }

    @classmethod
    def set_values(cls, x, y, z):
        cls.values = [x, y, z]
