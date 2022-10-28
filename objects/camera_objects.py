from pydeation.objects.abstract_objects import ProtoObject
from pydeation.xpresso.userdata import *
from pydeation.xpresso.xpressions import *
from pydeation.animation.animation import ScalarAnimation, AnimationGroup
from pydeation.constants import ASPECT_RATIO
import c4d

# desried features:
# ThreeDCamera:
# - continuous rotation around point
# - focus on specific object with optional normal vector
# - zoom in and out
# TwoDCamera:
# - move around in 2D
# - zoom in and out
# - focus on specific object


class TwoDCamera(ProtoObject):

    def __init__(self, frame_width=500, **kwargs):
        self.frame_width = frame_width
        super().__init__(**kwargs)
        self.parameters = []
        self.specify_parameters()
        self.insert_parameters()
        self.specify_relations()

    def specify_object(self):
        self.obj = c4d.BaseObject(c4d.Ocamera)

    def set_object_properties(self):
        pass

    def specify_parameters(self):
        self.frame_width_parameter = ULength(
            name="FrameWidth", default_value=self.frame_width)
        self.parameters += [self.frame_width_parameter]

    def specify_relations(self):
        # zooming is reduced to the width of the camera frame as a function of the cameras distance from the xy plane
        distance_to_frame_width_ratio = -100/100
        frame_width_relation = XRelation(part=self, whole=self, desc_ids=[POS_Z],
                                        parameters=[self.frame_width_parameter], formula=f"{self.frame_width_parameter.name}*{distance_to_frame_width_ratio}")

    def set_unique_desc_ids(self):
        self.desc_ids = {
            "zoom": c4d.DescID(c4d.DescLevel(c4d.CAMERA_ZOOM, c4d.DTYPE_REAL, 0))
        }

    def focus_on(self, target, border=0.2):
        # moves and zooms such that the tragets bounding box is in the frame
        center = target.get_center()
        radius = target.get_radius()
        if radius[0] < radius[1]:
            self.frame_width = 2 * radius[1] * (1 +  border) * ASPECT_RATIO
        else:
            self.frame_width = 2 * radius[0] * (1 + border)

        desc_id = self.frame_width_parameter.desc_id
        move_animation = self.move(x=center[0], y=center[1])
        zoom_animation = ScalarAnimation(target=self, descriptor=desc_id, value_fin=self.frame_width)
        self.obj[desc_id] = self.frame_width
        animation = AnimationGroup(move_animation, zoom_animation)
        return animation

    def zoom(self, frame_width=None):
        if frame_width is None:
            frame_width = self.frame_width
        desc_id = self.frame_width_parameter.desc_id
        animation = ScalarAnimation(target=self, descriptor=desc_id, value_fin=frame_width)
        self.obj[desc_id] = frame_width
        return animation
