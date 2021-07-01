

from download_data import *
from movement_laws import *
from tqdm import tqdm
import cv2
from logger import logger
import subprocess


from movement_controller import MovementController
from sly_warnings import window_warner


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


def keep_annotations_by_frame(temp_objects, frame_index, ann_keeper):
    annotations_for_frame = []

    for curr_object in temp_objects:
        x, y = curr_object.controller.x, curr_object.controller.y
        curr_object_coords = sly.Rectangle(y, x, y + curr_object.image.shape[0] - 1,
                                           x + curr_object.image.shape[1] - 1)

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
        converted_path = video_path.replace("preview.mp4", "VP90preview.mp4")
        # ffmpeg -i input.mp4 -c:v libvpx-vp9 -c:a libopus output.webm
        subprocess.call(['ffmpeg', '-y', '-i', f'{video_path}', '-c:v', 'libvpx-vp9', '-c:a',
                         'libopus', f'{converted_path}'])
        os.remove(video_path)
        os.rename(converted_path, video_path)

    sly_progress.next_step()


