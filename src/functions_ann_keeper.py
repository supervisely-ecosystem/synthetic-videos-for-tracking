from logger import logger

from supervisely_lib.video_annotation.key_id_map import KeyIdMap
from init_api import *

from supervisely_lib.annotation.tag_meta import TagValueType


class AnnotationKeeper:
    def __init__(self, video_shape, current_objects, project_id=None):

        self.video_shape = video_shape

        if not project_id:
            self.new_project = api.project.create(WORKSPACE_ID, 'TEST', type=sly.ProjectType.VIDEOS,
                                                  change_name_if_conflict=True)
            self.new_dataset = api.dataset.create(self.new_project.id, f'ds_{self.new_project.id}',
                                                  change_name_if_conflict=True)
        else:
            self.new_dataset = api.dataset.get_list(project_id)[0]

        self.key_id_map = KeyIdMap()
        self.sly_objects_list = []
        self.video_object_list = []

        self.get_sly_objects(current_objects)
        self.get_video_objects_list()

        self.video_object_collection = sly.VideoObjectCollection(self.video_object_list)

        self.figures = []
        self.frames_list = []
        self.frames_collection = []

        self.meta = sly.ProjectMeta(obj_classes=sly.ObjClassCollection(self.sly_objects_list))

        if not project_id:
            api.project.update_meta(self.new_project.id, self.meta.to_json())


    def add_figures_by_frame(self, coords_data, class_names, frame_index):
        temp_figures = []
        object_labels = [temp_object.name for temp_object in self.sly_objects_list]
        for index, current_coord in enumerate(coords_data):
            object_index = object_labels.index(class_names[index])
            temp_figures.append(sly.VideoFigure(self.video_object_list[object_index], current_coord, frame_index))

        self.figures.append(temp_figures)

    def upload_annotation(self, video_path):

        self.get_frames_list()
        self.frames_collection = sly.FrameCollection(self.frames_list)

        video_annotation = sly.VideoAnnotation(self.video_shape, len(self.frames_list),
                                  self.video_object_collection, self.frames_collection)
            # .to_json(self.key_id_map)

        # converted_video_annotation = sly.VideoAnnotation.from_json(video_annotation, self.meta)

        video_name = video_path.split('/')[-1]
        file_info = api.video.upload_paths(self.new_dataset.id, [video_name], [video_path])
        api.video.annotation.append(file_info[0].id, video_annotation)

        logger.info(f'{video_name} uploaded!')


    def get_sly_objects(self, current_objects):
        for obj in current_objects:
            # @TODO: to add different types shapes
            if obj.class_name not in [temp_object.name for temp_object in self.sly_objects_list]:
                self.sly_objects_list.append(sly.ObjClass(obj.class_name, sly.Rectangle))

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
