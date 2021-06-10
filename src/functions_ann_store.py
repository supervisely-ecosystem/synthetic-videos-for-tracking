import supervisely_lib as sly
from supervisely_lib.video_annotation.key_id_map import KeyIdMap


class AnnotationKeeper:
    def __init__(self, current_objects, video_shape):
        self.video_shape = video_shape

        self.key_id_map = KeyIdMap()
        self.sly_objects_list = []
        self.video_object_list = []

        self.get_sly_objects(current_objects)
        self.get_video_objects_list()

        self.video_object_collection = sly.VideoObjectCollection(self.video_object_list)

        self.figures = []
        self.frames_list = []
        self.frames_collection = []

        self.meta = sly.ProjectMeta(obj_classes=sly.ObjClassCollection(self.sly_objects_list),
                                    project_type=sly.VideoProject)

    def add_figures_by_frame(self, coords_data, frame_index):
        temp_figures = []
        for index, current_coord in enumerate(coords_data):
            temp_figures.append(sly.VideoFigure(self.video_object_list[index], current_coord, frame_index))

        self.figures.append(temp_figures)

    def save_annotation(self):
        """TODO: upload to SLY function"""
        self.get_frames_list()
        self.frames_collection = sly.FrameCollection(self.frames_list)

        ann = sly.VideoAnnotation(self.video_shape, 333, self.video_object_collection, self.frames_collection)

        ann.to_json(self.key_id_map)

    def get_sly_objects(self, current_objects):
        for obj in current_objects:
            self.sly_objects_list.append(sly.ObjClass(obj.name, sly.Rectangle))

    def get_video_objects_list(self):
        for sly_object in self.sly_objects_list:
            self.video_object_list.append(sly.VideoObject(sly_object))

    def get_frames_list(self):
        for index, figure in enumerate(self.figures):
            self.frames_list.append(sly.Frame(index, figure))




###

###



#
# for curr_object in temp_objects:
#     sly.Rectangle(curr_object.controller.x,
#                   curr_object.controller.y,
#                   x + curr_object.image.shape[0],
#                   y + curr_object.image.shape[1])
