import cv2
import numpy
from tqdm import tqdm

from movement_controller import MovementController

from logger import logger


def add_object_to_background(background, overlay, x, y):
    """
    Добавляет объект overlay на фон background
    :param background: фоновое изображение
    :param overlay: объект, который нужно добавить
    :param x: координата background x, на которую будет нанесен overlay от левого верхнего угла
    :param y: координата background y, на которую будет нанесен overlay от левого верхнего угла
    :return: совмещенное изображение
    """

    background_width = background.shape[1]
    background_height = background.shape[0]

    if x >= background_width or y >= background_height:
        return background

    h, w = overlay.shape[0], overlay.shape[1]

    if x + w > background_width:
        w = background_width - x
        overlay = overlay[:, :w]

    if y + h > background_height:
        h = background_height - y
        overlay = overlay[:h]

    if overlay.shape[2] < 4:
        overlay = numpy.concatenate(
            [
                overlay,
                numpy.ones((overlay.shape[0], overlay.shape[1], 1), dtype=overlay.dtype) * 255
            ],
            axis=2,
        )

    overlay_image = overlay[..., :3]
    mask = overlay[..., 3:] / 255.0

    background[y:y+h, x:x+w] = (1.0 - mask) * background[y:y+h, x:x+w] + mask * overlay_image

    return background


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


def generate_frames(duration, fps, background, temp_objects, movement_law, speed_interval):
    """
    Генерирует кадры видео на основе параметров
    :param duration: длительность в секундах
    :param fps: количество кадров в секунду
    :param background: фоновое изображение
    :param temp_objects: объекты для вставки в кадр
    :param movement_law: закон перемещения объектов
    :param speed_interval: интервал скорости перемещения объектов
    :return: сгенерированные кадры
    """

    for curr_object in temp_objects:

        curr_object.controller = MovementController(movement_law=movement_law(),
                                                    speed_interval=speed_interval,
                                                    self_overlay=1,
                                                    x_high_limit=background.shape[1] - curr_object.image.shape[1],
                                                    y_high_limit=background.shape[0] - curr_object.image.shape[0],
                                                    x_low_limit=0,
                                                    y_low_limit=0)

    frames = []

    for _ in tqdm(range(fps * duration), desc='Objects to background: '):
        frame_background = background.copy()
        added_objects = []
        for curr_object in temp_objects:

            x, y = curr_object.controller.next_step(added_objects, curr_object)
            frame_background = add_object_to_background(
                frame_background, curr_object.image, x, y)

            added_objects.append(curr_object)
        frames.append(frame_background)
        # cv2.imshow(f'frame {len(frames)}', frame_background)
        # cv2.waitKey()

    return frames


def write_frames_to_file(video_name, fps, frames, video_shape):
    """
    Записывает кадры в единный видеофайл
    :param video_name: название видео
    :param fps: количество кадров
    :param frames: кадры, которые нужно склеить
    :param video_shape: размер видеокадра
    :return: None
    """
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(video_name, fourcc, fps, video_shape)

    for frame in tqdm(frames, desc='Generating video file: '):
        video.write(frame)

    video.release()



