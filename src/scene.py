from functions_background import *
from functions_objects import *
from functions_video import *

from transformations import get_transforms

from functions_ann_keeper import AnnotationKeeper


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


def process_video(sly_progress, state, is_preview=True):
    req_objects = state['req_objects']
    req_backgrounds = state['req_backgrounds']

    _, minor_transform, frame_transform = get_transforms(5)

    background_paths = [curr_background.image_path for curr_background in req_backgrounds]

    custom_scene = Scene(object_general_transforms=None, object_minor_transforms=minor_transform,
                         frame_transform=frame_transform)

    if is_preview:
        custom_scene.add_backgrounds([background_paths[random.randint(0, len(background_paths) - 1)]])
    else:
        custom_scene.add_backgrounds(background_paths)

    custom_scene.add_objects(req_objects)

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

    custom_scene.generate_video(video_path=video_path,  # generate video
                                duration=duration,
                                fps=fps,
                                movement_laws=movement_laws,
                                self_overlay=tuple(state['objectOverlayInterval']),
                                speed_interval=tuple(state['speedInterval']),
                                project_id=None,
                                project_name=state["resProjectName"],
                                upload_ann=False if is_preview else True,
                                sly_progress=sly_progress
                                )

    if custom_scene.ann_keeper.project:
        return custom_scene.ann_keeper.project.id
