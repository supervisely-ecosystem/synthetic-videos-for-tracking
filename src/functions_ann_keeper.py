from logger import logger

from supervisely_lib.video_annotation.key_id_map import KeyIdMap
from init_api import *

from supervisely_lib.annotation.tag_meta import TagValueType


class AnnotationKeeper:
    def __init__(self, video_shape, current_objects):

        self.video_shape = video_shape

        self.project = None
        self.dataset = None
        self.meta = None

        self.key_id_map = KeyIdMap()
        self.sly_objects_list = []
        self.video_object_list = []

        self.get_sly_objects(current_objects)
        self.get_video_objects_list()

        self.video_object_collection = sly.VideoObjectCollection(self.video_object_list)

        self.figures = []
        self.frames_list = []
        self.frames_collection = []

    def add_figures_by_frame(self, coords_data, frame_index):
        temp_figures = []
        for index, current_coord in enumerate(coords_data):
            temp_figures.append(sly.VideoFigure(self.video_object_list[index], current_coord, frame_index))

        self.figures.append(temp_figures)

    def init_project_remotely(self, project_id=None, project_name='vSynth'):
        if not project_id:
            self.project = api.project.create(WORKSPACE_ID, project_name, type=sly.ProjectType.VIDEOS,
                                              change_name_if_conflict=True)
            self.dataset = api.dataset.create(self.project.id, f'ds_{self.project.id}',
                                              change_name_if_conflict=True)
        else:
            self.dataset = api.dataset.get_list(project_id)[0]

        self.meta = sly.ProjectMeta(obj_classes=sly.ObjClassCollection(self.get_unique_objects(self.sly_objects_list)))

        if not project_id:
            api.project.update_meta(self.project.id, self.meta.to_json())

    def upload_annotation(self, video_path):
        self.get_frames_list()
        self.frames_collection = sly.FrameCollection(self.frames_list)

        video_annotation = sly.VideoAnnotation(self.video_shape, len(self.frames_list),
                                               self.video_object_collection, self.frames_collection)

        video_name = video_path.split('/')[-1]
        file_info = api.video.upload_paths(self.dataset.id, [video_name], [video_path])
        api.video.annotation.append(file_info[0].id, video_annotation)

        logger.info(f'{video_name} uploaded!')


    def get_unique_objects(self, obj_list):
        unique_objects = []
        for obj in obj_list:
            # @TODO: to add different types shapes
            if obj.name not in [temp_object.name for temp_object in unique_objects]:
                unique_objects.append(obj)

        return unique_objects

    def get_sly_objects(self, current_objects):
        for obj in current_objects:
            # @TODO: to add different types shapes
            # if obj.class_name not in [temp_object.name for temp_object in self.sly_objects_list]:
            self.sly_objects_list.append(sly.ObjClass(obj.class_name, sly.Rectangle))

    def get_video_objects_list(self):
        for sly_object in self.sly_objects_list:
            self.video_object_list.append(sly.VideoObject(sly_object))

    def get_frames_list(self):
        for index, figure in enumerate(self.figures):
            self.frames_list.append(sly.Frame(index, figure))
