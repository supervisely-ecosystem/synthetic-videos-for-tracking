from functions_background import *
from functions_objects import *
from functions_video import *
from movement_laws import *

from transformations import get_transforms

from functions_ann_keeper import AnnotationKeeper

from init_ui import *

import random

import copy


class Scene:
    def __init__(self, width=1920, height=1080, object_general_transforms=None,
                 object_minor_transforms=None, frame_transform=None):
        self.width = width
        self.height = height
        self.backgrounds = []

        self.base_primitives = []
        self.base_primitives_backup = []

        self.req_objects_num = {}

        self.object_general_transforms = object_general_transforms
        self.object_minor_transforms = object_minor_transforms
        self.frame_transform = frame_transform

        self.ann_keeper = None

    def add_backgrounds(self, background_paths):
        for background_path in background_paths:
            self.backgrounds.append(get_cv2_background_by_path(background_path))
        logger.info(f'{len(self.backgrounds)} backgrounds successfully added')

    def add_objects(self, req_objects, state):

        self.base_primitives = get_objects_list_for_project(req_objects)
        self.base_primitives_backup = get_objects_list_for_project(req_objects)
        self.req_objects_num = state['classCounts']

        logger.info(f'[{len(self.base_primitives)}] objects successfully added')
        logger.info(f'available objects:\n'
                    f'{get_available_objects(self.base_primitives)}\n')

    def generate_video(self, video_path, fps, duration, movement_laws, state, upload_ann=False, sly_progress=None):

        self_overlay = tuple(state['objectOverlayInterval'])
        speed_interval = tuple(state['speedInterval'])
        project_name = state["dstProjectName"]
        ds_name = state["dstDatasetName"]
        project_id = state["dstProjectId"]
        ds_id = state["selectedDatasetName"]

        sly_progress_backgrounds = SlyProgress(api, task_id, 'progress4')
        sly_progress_backgrounds.refresh_params('Video', len(self.backgrounds))

        for curr_background in self.backgrounds:

            temp_objects = copy.deepcopy(self.base_primitives)
            temp_objects = generate_base_primitives(temp_objects, self.req_objects_num,
                                                    curr_background, self.object_general_transforms,
                                                    state['canResize'])
            if len(temp_objects) > 0:
                initialize_controllers(temp_objects, movement_laws, speed_interval,
                                       self_overlay, curr_background.shape,
                                       general_transforms=self.object_general_transforms,
                                       minor_transforms=self.object_minor_transforms)

                self.ann_keeper = AnnotationKeeper(video_shape=curr_background.shape,
                                                   current_objects=temp_objects)

                frames = generate_frames(fps, duration, curr_background, temp_objects, self.ann_keeper,
                                         self.frame_transform,
                                         sly_progress)

                if not frames:
                    return -3

                video_shape = (curr_background.shape[1], curr_background.shape[0])
                write_frames_to_file(video_path, fps, frames, video_shape, sly_progress)

                if upload_ann:
                    sly_progress.refresh_params('Uploading annotations', 1)

                    self.ann_keeper.init_project_remotely(project_id=project_id, project_name=project_name,
                                                          ds_id=ds_id, ds_name=ds_name)
                    self.ann_keeper.upload_annotation(video_path)
                    project_id = self.ann_keeper.project.id
                    ds_id = self.ann_keeper.dataset.name

                    sly_progress.next_step()

                sly_progress_backgrounds.next_step()
            else:
                return -2
        return 0


def process_video(sly_progress, state, is_preview=True):
    req_objects = load_dumped('req_object.pkl')
    req_backgrounds = load_dumped('req_backgrounds.pkl')
    augs = load_dumped('augmentations.pkl')

    base_transform, minor_transform, frame_transform = get_transforms(augs)

    background_paths = [curr_background.image_path for curr_background in req_backgrounds]

    custom_scene = Scene(object_general_transforms=base_transform, object_minor_transforms=minor_transform,
                         frame_transform=frame_transform)

    if is_preview:
        # custom_scene.add_backgrounds([background_paths[random.randint(0, len(background_paths) - 1)]])
        custom_scene.add_backgrounds([background_paths[0]])
    else:
        custom_scene.add_backgrounds(background_paths)

    custom_scene.add_objects(req_objects, state)

    fps = state['fps']

    if is_preview:
        duration = state['durationPreview']
    else:
        duration = state['durationVideo']

    if is_preview:
        video_path = os.path.join(app.data_dir, './preview.mp4')
    else:
        video_path = os.path.join(app.data_dir, f'./{duration}sec_{fps}fps.mp4')

    movement_laws = load_movements_laws(custom_scene=custom_scene,
                                        req_laws={'linearLaw': state['linearLaw'],
                                                  'randomLaw': state['randomLaw']})

    rc = custom_scene.generate_video(video_path=video_path,  # generate video
                                     duration=duration,
                                     fps=fps,
                                     movement_laws=movement_laws,
                                     state=state,
                                     upload_ann=False if is_preview else True,
                                     sly_progress=sly_progress,
                                     )
    if rc < 0:
        return rc, None

    if not is_preview:
        return rc, custom_scene.ann_keeper.project.id

@app.callback("apply_synth_settings")
@sly.timeit
@app.ignore_errors_and_show_dialog_window()
def apply_synth_settings(api: sly.Api, task_id, context, state, app_logger):
    fields = [
        {"field": "state.done4", "payload": True},
        {"field": "state.collapsed5", "payload": False},
        {"field": "state.disabled5", "payload": False},
        {"field": "state.activeStep", "payload": 5},
    ]
    api.app.set_fields(task_id, fields)
    api.app.set_field(task_id, "data.scrollIntoView", f"step{5}")
