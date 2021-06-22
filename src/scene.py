from functions_background import *
from functions_objects import *
from functions_video import *

from functions_ann_keeper import AnnotationKeeper

from movement_laws import *

import imgaug.augmenters as iaa

import numpy


class Scene:
    def __init__(self, width=1920, height=1080, object_general_transforms=None,
                 object_minor_transforms=None, frame_transform=None):
        self.width = width
        self.height = height
        self.backgrounds = []
        self.objects = []
        self.object_general_transforms = object_general_transforms
        self.object_minor_transforms = object_minor_transforms
        self.frame_transform = frame_transform

        self.ann_keeper = None

    def add_backgrounds(self, background_paths):
        for background_path in background_paths:
            self.backgrounds.append(get_cv2_background_by_path(background_path))
        logger.info(f'{len(self.backgrounds)} backgrounds successfully added')

    def add_objects(self, req_objects):

        self.objects = get_objects_list_for_project(req_objects)

        logger.info(f'[{len(self.objects)}] objects successfully added')
        logger.info(f'available objects:\n'
                    f'{get_available_objects(self.objects)}\n')

    def generate_video(self, video_path, fps, duration, movement_laws, self_overlay,
                       speed_interval,
                       project_id=None, project_name='SLYvSynth',
                       upload_ann=False, sly_progress=None):

        for curr_background in self.backgrounds:

            temp_objects = self.objects
            initialize_controllers(temp_objects, movement_laws, speed_interval,
                                   self_overlay, curr_background.shape,
                                   general_transforms=self.object_general_transforms,
                                   minor_transforms=self.object_minor_transforms)

            ann_keeper = AnnotationKeeper(video_shape=curr_background.shape,
                                          current_objects=temp_objects)

            frames = generate_frames(fps, duration, curr_background, temp_objects, ann_keeper, self.frame_transform,
                                     sly_progress)

            video_shape = (curr_background.shape[1], curr_background.shape[0])
            write_frames_to_file(video_path, fps, frames, video_shape, sly_progress)

            if upload_ann:
                ann_keeper.init_project_remotely(project_id=project_id, project_name=project_name)
                ann_keeper.upload_annotation(video_path)

                project_id = ann_keeper.project.id
            self.ann_keeper = ann_keeper

