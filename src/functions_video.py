import copy

from sly_globals import *

from tqdm import tqdm
import cv2
import subprocess
import numpy
import random

from logger import logger

from sly_warnings import window_warner
from augmentations import get_transforms
from download_data import download_images, SlyProgress
from movement_laws import load_movements_laws

from functions_objects import get_objects_list_for_project, get_available_objects, generate_object_counts, \
    generate_base_primitives

from movement_controller import MovementController
from functions_ann_keeper import AnnotationKeeper
from functions_background import get_cv2_background_by_path


class Scene:
    def __init__(self, width=1920, height=1080, object_general_transforms=None,
                 object_minor_transforms=None, frame_transform=None):
        self.width = width
        self.height = height
        self.backgrounds = []

        self.base_primitives = []
        self.base_primitives_backup = []

        self.req_objects_num = None

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
        self.req_objects_num = (state['classCountsMin'], state['classCountsMax'])

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

            req_objects_num = generate_object_counts(self.req_objects_num[0], self.req_objects_num[1])

            temp_objects = copy.deepcopy(self.base_primitives)
            temp_objects = generate_base_primitives(temp_objects, req_objects_num,
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
                    sly_progress_backgrounds.reset_params()
                    return -3

                video_shape = (curr_background.shape[1], curr_background.shape[0])
                write_frames_to_file(video_path, fps, frames, video_shape, sly_progress)

                if upload_ann:
                    self.ann_keeper.init_project_remotely(project_id=project_id, project_name=project_name,
                                                          ds_id=ds_id, ds_name=ds_name)
                    self.ann_keeper.upload_annotation(video_path, sly_progress)
                    project_id = self.ann_keeper.project.id
                    ds_id = self.ann_keeper.dataset.name

                sly_progress_backgrounds.next_step()

            else:
                sly_progress_backgrounds.reset_params()
                sly_progress.reset_params()
                return -2

        sly_progress_backgrounds.reset_params()

        return 0


def initialize_controllers(temp_objects, movement_laws, speed_interval, self_overlay, background_shape,
                           general_transforms=None,
                           minor_transforms=None):

    for curr_object in temp_objects:

        movement_law = numpy.random.choice(movement_laws)
        curr_law = movement_law['law']
        curr_params = movement_law['params']

        curr_object.controller = MovementController(curr_object=curr_object,
                                                    movement_law=curr_law(*curr_params),
                                                    speed_interval=speed_interval,
                                                    self_overlay=self_overlay,  # how much the object can be covered
                                                    background_shape=background_shape,
                                                    general_transforms=general_transforms,
                                                    minor_transforms=minor_transforms)

@app.callback("apply_synth_settings")
@sly.timeit
@app.ignore_errors_and_show_dialog_window()
def apply_synth_settings(api: sly.Api, task_id, context, state, app_logger):
    fields = [
        {"field": "state.done5", "payload": True},
        {"field": "state.collapsed6", "payload": False},
        {"field": "state.disabled6", "payload": False},
        {"field": "state.activeStep", "payload": 6},
    ]
    api.app.set_fields(task_id, fields)
    api.app.set_field(task_id, "data.scrollIntoView", f"step{6}")


def add_object_to_background(background, curr_object):
    """
    Добавляет объект curr_object на фон background
    :param background: фоновое изображение
    :param curr_object: объект, который нужно добавить

    :return: совмещенное изображение
    """

    x = curr_object.controller.x
    y = curr_object.controller.y

    fg = curr_object.image
    fg_mask = curr_object.mask.astype(numpy.uint8)

    fg_mask = fg_mask * 255

    sec_h, sec_w, _ = fg.shape
    mask_inv = cv2.bitwise_not(fg_mask)

    img1_bg = cv2.bitwise_and(background[y:y+sec_h, x:x+sec_w, :],
                              background[y:y+sec_h, x:x+sec_w, :], mask=mask_inv)

    img2_fg = cv2.bitwise_and(fg, fg, mask=fg_mask)
    dst = cv2.add(img1_bg, img2_fg)

    background[y:y+sec_h, x:x+sec_w, :] = dst


def load_required_objects(objects_dict, objects_list):
    """
    Загружает объекты запрошенные пользователем из списка извлеченных объектов датасета
    :param objects_dict: запрошенные пользователем объекты
    :param objects_list: извлеченные из датасета объекты
    :return: список запрошенных-извлеченных объектов
    """
    required_objects = []
    for class_name, count in objects_dict.items():
        temp_counter = 0
        for curr_obj in objects_list:
            if curr_obj.class_name == class_name:
                required_objects.append(curr_obj)
                temp_counter += 1
                if temp_counter == count:
                    break

    if len(required_objects) > 0:
        return required_objects
    else:
        logger.warning('cannot find any fitting objects to generate video')
        raise ValueError('objects is missing')


def keep_annotations_by_frame(temp_objects, frame_index, ann_keeper):
    annotations_for_frame = []

    for curr_object in temp_objects:
        if curr_object.is_tracking:
            x, y = curr_object.controller.x, curr_object.controller.y
            curr_object_coords = sly.Rectangle(y, x, y + curr_object.image.shape[0] - 1,
                                               x + curr_object.image.shape[1] - 1)
        else:
            curr_object_coords = None
        annotations_for_frame.append(curr_object_coords)

    ann_keeper.add_figures_by_frame(annotations_for_frame, frame_index)


def generate_frames(duration, fps, background, temp_objects, ann_keeper=None, frame_transform=None, sly_progress=None):
    """
    Генерирует кадры видео на основе параметров
    :param duration: длительность в секундах
    :param fps: количество кадров в секунду
    :param background: фоновое изображение
    :param temp_objects: объекты для вставки в кадр
    :param ann_keeper: хранитель аннотаций формата SLY
    :param frame_transform: transformations for frame
    :param sly_progress: progress bar
    :return: сгенерированные кадры
    """

    frames = []

    if sly_progress:
        sly_progress.refresh_params('Objects to background', int(fps * duration))

    for frame_index in tqdm(range(fps * duration), desc='Objects to background: '):
    # for frame_index in range(fps * duration):
        frame_background = background.copy()
        added_objects = []
        for curr_object in temp_objects:
            rc = curr_object.controller.next_step(added_objects, curr_object)

            if rc == -1:
                window_warner('Too many collisions occurred between objects during video generation.'
                              'Please allow objects to overlap each other more, or reduce the objects count.',
                              fields=[{"field": "state.previewLoading", "payload": False},
                                      {"field": "data.videoUrl", "payload": None}])
                return None

            add_object_to_background(
                frame_background, curr_object)
            added_objects.append(curr_object)

        if frame_transform:
            frame_background = frame_transform(image=frame_background)
        frames.append(frame_background)

        if ann_keeper:
            keep_annotations_by_frame(added_objects, frame_index, ann_keeper)

        if sly_progress:
            sly_progress.next_step()

    return frames


def write_frames_to_file(video_path, fps, frames, video_shape, sly_progress=None):
    """
    Записывает кадры в единный видеофайл
    :param video_path: название видео
    :param fps: количество кадров
    :param frames: кадры, которые нужно склеить
    :param video_shape: размер видеокадра
    :return: None
    """
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(video_path, fourcc, fps, video_shape)

    sly_progress.refresh_params('Generating video file', len(frames))

#     for frame in tqdm(frames, desc='Generating video file: '):
    for frame in frames:
        video.write(frame)
    
        sly_progress.next_step()

    sly_progress.refresh_params('Saving video file', 1)

    video.release()

    if video_path.split('/')[-1] == 'preview.mp4':
        converted_path = video_path.replace("preview.mp4", "converted_preview.mp4")
        # ffmpeg -i input.mp4 -c:v libvpx-vp9 -c:a libopus output.webm
        subprocess.call(['ffmpeg', '-y', '-i', f'{video_path}', '-c:v', 'libx264', '-c:a',
                         'libopus', f'{converted_path}'])
        os.remove(video_path)
        os.rename(converted_path, video_path)

    sly_progress.next_step()


def process_video(sly_progress, state, is_preview=True):
    req_objects = load_dumped('req_objects.pkl')
    req_backgrounds = load_dumped('req_backgrounds.pkl')
    augs = load_dumped('augmentations.pkl')

    base_transform, minor_transform, frame_transform = get_transforms(augs)
    custom_scene = Scene(object_general_transforms=base_transform, object_minor_transforms=minor_transform,
                         frame_transform=frame_transform)

    if is_preview:  # caching backgrounds
        req_backgrounds = [req_backgrounds[random.randint(0, len(req_backgrounds) - 1)]]
    else:
        while len(req_backgrounds) < state['videoSynthNum']:
            req_backgrounds.extend(req_backgrounds)
        random.shuffle(req_backgrounds)
        req_backgrounds = req_backgrounds[:state['videoSynthNum']]

    download_images(req_backgrounds, 'backgrounds', sly_progress, need_reset_progress=False)
    background_paths = [curr_background.image_path for curr_background in req_backgrounds]

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
        return rc, -1

    if not is_preview:
        return rc, custom_scene.ann_keeper.project.id

    return rc, None

