from pydeation.animation.animation import VectorAnimation, AnimationGroup
from pydeation.animation.object_animators import Show, Hide
from abc import ABC, abstractmethod
from collections import defaultdict
import c4d


class Scene(ABC):
    """abstract class acting as blueprint for scenes"""

    def __init__(self, resolution="default"):
        self.resolution = resolution
        self.create_new_document()
        self.set_scene_name()
        self.insert_document()
        self.construct()
        self.set_interactive_render_region()
        self.set_render_settings()

    def set_render_settings(self):
        self.render_settings = RenderSettings()
        self.render_settings.set_resolution(self.resolution)

    def create_new_document(self):
        """creates a new project and gets the active document"""
        self.document = c4d.documents.BaseDocument()
        c4d.documents.InsertBaseDocument(self.document)

    @abstractmethod
    def construct(self):
        """here the actual scene consisting out of objects and animations is constructed
        this method should be overwritten by the inheriting scene classes"""
        pass

    @property
    def scene_name(self):
        """holds the scene name"""
        return self._scene_name

    @scene_name.setter
    def scene_name(self, name):
        self._scene_name = name

    def set_scene_name(self):
        """sets the scene name and the document name"""
        self.scene_name = self.__class__.__name__
        self.document.SetDocumentName(self.scene_name)

    def insert_document(self):
        """inserts the document into cinema"""
        c4d.documents.InsertBaseDocument(self.document)

    def set_interactive_render_region(self):
        """creates an IRR window over the full size of the editor view"""
        c4d.CallCommand(600000017)  # call IRR script by ID
        c4d.EventAdd()
        # workaround because script needs to be executed from main thread not pydeation library
        # ID changes depending on machine
        # CHANGE THIS IN FUTURE TO MORE ROBUST SOLUTION

    def group_animations_by_obj(self, animations):
        """sorts the animations by their target"""
        animations_grouped_by_obj = defaultdict(list)
        for animation in animations:
            animations_grouped_by_obj[animation.target].append(animation)
        return animations_grouped_by_obj

    def group_obj_animations_by_desc_id(self, obj_animations):
        """sorts the animations by their description id"""
        obj_animations_grouped_by_desc_id = defaultdict(list)
        for obj_animation in obj_animations:
            obj_animations_grouped_by_desc_id[obj_animation.param_id].append(
                obj_animation)
        return obj_animations_grouped_by_desc_id

    def sort_desc_id_animations_chronologically(self, desc_id_animations):
        """sorts animations chronologically by the relative run times"""
        desc_id_animations_chronological = sorted(
            desc_id_animations, key=lambda x: x.rel_start)
        return desc_id_animations_chronological

    def link_animation_chains(self, animations):
        """sorts the animation by target and description id to identify and link animation chains
        (sets initial value of following animation equal to final value of preceding one)"""

        linked_animations = []
        animations_grouped_by_obj = self.group_animations_by_obj(
            animations)  # group animations by object
        for obj_animations in animations_grouped_by_obj.values():
            obj_animations_grouped_by_desc_id = self.group_obj_animations_by_desc_id(
                obj_animations)  # group animations by desc id
            for desc_id_animations in obj_animations_grouped_by_desc_id.values():
                desc_id_animations_chronological = self.sort_desc_id_animations_chronologically(
                    desc_id_animations)  # sort animations chronologically
                for i, desc_id_animation in enumerate(desc_id_animations_chronological):
                    # only link vector animaitons
                    if type(desc_id_animation) is VectorAnimation:
                        # link chain according to type relative/absolute
                        previous_animations = desc_id_animations_chronological[:i]
                        # shift vector by all previous vectors
                        if desc_id_animation.relative:
                            for previous_animation in previous_animations:
                                desc_id_animation += previous_animation
                        # shift initial value by all previous vectors
                        else:
                            vectors = []
                            for previous_animation in previous_animations:
                                vector = previous_animation.get_vector()  # get vector
                                vectors.append(vector)  # collect vector
                            value_ini = sum(vectors) + \
                                desc_id_animation.value_ini
                            desc_id_animation.set_value_ini(
                                value_ini)  # set new value

                linked_animations += desc_id_animations_chronological

        return linked_animations

    def feed_run_time(self, animations, run_time):
        """feeds the run time to animations"""
        for animation in animations:
            animation.abs_run_time = run_time

    def execute_animations(self, animations):
        """passes the run time to animations and executes them"""
        for animation in animations:
            animation.execute()

    def add_time(self, run_time):
        """passes the run time in the document timeline"""
        time_ini = self.document.GetTime()
        time_fin = time_ini + c4d.BaseTime(run_time)
        self.document.SetTime(time_fin)
        c4d.EventAdd()  # update cinema

    def flatten(self, animations):
        """flattens animations by wrapping them inside animation group"""
        animation_group = AnimationGroup(*animations)
        flattened_animations = animation_group.animations
        return flattened_animations

    def add_show_animation(self, animation_group):
        """adds a show animator in the beginning of the animation group"""
        objs = animation_group.get_objs()
        min_rel_start = animation_group.get_min_rel_start()
        animation_group_with_show = AnimationGroup(
            (Show(*objs), (min_rel_start, min_rel_start)), animation_group)  # we use a zero length tuple to keep compatibility with vector animations
        return animation_group_with_show

    def add_hide_animation(self, animation_group):
        """adds a show animator in the beginning of the animation group"""
        objs = animation_group.get_objs()
        max_rel_stop = animation_group.get_max_rel_stop()
        animation_group_with_hide = AnimationGroup(
            (Hide(*objs), (max_rel_stop, max_rel_stop)), animation_group)  # we use a zero length tuple to keep compatibility with vector animations
        return animation_group_with_hide

    def handle_visibility(self, animations):
        """adds visibility animators depending on the category of the animation group"""
        animation_groups_with_visibility = []
        for animation in animations:
            if type(animation) is AnimationGroup:
                animation_group = animation  # is animation group
                if animation_group.category == "constructive":
                    animation_group_with_visibility = self.add_show_animation(
                        animation_group)
                elif animation_group.category == "destructive":
                    animation_group_with_visibility = self.add_hide_animation(
                        animation_group)
                else:
                    animation_group_with_visibility = animation_group
                animation_groups_with_visibility.append(
                    animation_group_with_visibility)
            else:
                animation_groups_with_visibility.append(animation)
        return animation_groups_with_visibility

    def play(self, *animations, run_time=1):
        """handles several tasks for the animations:
            - handles visibility
            - flattens animations
            - links animation chains
            - feeds them the run time
            - executes the animations"""
        animations_with_visibility = self.handle_visibility(animations)
        flattened_animations = self.flatten(animations_with_visibility)
        linked_animations = self.link_animation_chains(flattened_animations)
        self.feed_run_time(linked_animations, run_time)
        self.execute_animations(linked_animations)
        self.add_time(run_time)

    def wait(self, seconds=1):
        """adds time without any animations"""
        self.add_time(seconds)


class RenderSettings():
    """holds and writes the render settings to cinema"""

    def __init__(self):
        self.document = c4d.documents.GetActiveDocument()  # get document
        self.set_base_settings()
        self.set_sketch_settings()

    def set_base_settings(self):
        """sets the base settings"""
        self.settings = self.document.GetActiveRenderData()

        # set parameters
        self.settings[c4d.RDATA_FRAMESEQUENCE] = 3  # set range to preview
        self.settings[c4d.RDATA_FORMAT] = 1125  # set to MP4

    def set_resolution(self, resolution):
        """sets the resolution for the render"""

        if resolution == "verylow":
            self.settings[c4d.RDATA_XRES] = 320
            self.settings[c4d.RDATA_YRES] = 180
        elif resolution == "low":
            self.settings[c4d.RDATA_XRES] = 480
            self.settings[c4d.RDATA_YRES] = 270
        elif resolution == "default":
            self.settings[c4d.RDATA_XRES] = 1280
            self.settings[c4d.RDATA_YRES] = 720
        elif resolution == "high":
            self.settings[c4d.RDATA_XRES] = 2560
            self.settings[c4d.RDATA_YRES] = 1440
        elif resolution == "veryhigh":
            self.settings[c4d.RDATA_XRES] = 3840
            self.settings[c4d.RDATA_YRES] = 2160

    def set_sketch_settings(self):
        """sets the sketch and toon settings"""

        sketch_vp = c4d.documents.BaseVideoPost(
            1011015)  # add sketch render settings
        # set parameters
        sketch_vp[c4d.OUTLINEMAT_SHADING_BACK_COL] = c4d.Vector(
            0, 0, 0)  # set background to black
        sketch_vp[c4d.OUTLINEMAT_SHADING_OBJECT] = False  # disable shading
        # set independent of pixel units
        sketch_vp[c4d.OUTLINEMAT_PIXELUNITS_INDEPENDENT] = True
        # show lines in editor view
        sketch_vp[c4d.OUTLINEMAT_EDLINES_SHOWLINES] = True
        sketch_vp[c4d.OUTLINEMAT_EDLINES_LINE_DRAW] = 1  # 3D lines in editor
        # set to custom mode
        sketch_vp[c4d.OUTLINEMAT_PIXELUNITS_INDEPENDENT_MODE] = 1
        sketch_vp[c4d.OUTLINEMAT_PIXELUNITS_BASEW] = 1280  # set custom width
        sketch_vp[c4d.OUTLINEMAT_PIXELUNITS_BASEH] = 700  # set custom height
        sketch_vp[c4d.OUTLINEMAT_EDLINES_REDRAW_FULL] = True  # redraw lines
        sketch_vp[c4d.OUTLINEMAT_LINE_SPLINES] = True  # enable splines

        self.settings.InsertVideoPost(
            sketch_vp)  # insert sketch settings
