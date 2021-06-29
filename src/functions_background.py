from logger import logger

import cv2
import os
import glob

import functions_objects


def get_cv2_background_by_path(background_path):
    """
    функция открывает изображение и возвращает объект cv2
    :param background_path: путь к изображению
    :return: объект изображения cv2
    """
    if not os.path.isfile(background_path):
        logger.error(f'{background_path} is broken')
        raise ValueError('Background path is broken')

    try:
        bg_img = cv2.imread(background_path)
        # return cv2.cvtColor(bg_img, cv2.COLOR_RGBA2BGRA)
        return bg_img
    except Exception as ex:
        logger.error(f'exception while opening file'
                     f'{ex}')
        raise ex


def object_larger_than_background(curr_object, curr_background):
    background_shape = curr_background.shape
    object_shape = curr_object.shape

    if (object_shape[0] >= background_shape[0]) or (object_shape[1] >= background_shape[1]):
        return True
    else:
        return False


def objects_larger_than_backgrounds(req_objects, req_backgrounds):
    objects_images = functions_objects.load_objects_images(req_objects)
    backgrounds_images = load_backgrounds_images(req_backgrounds)

    for backgrounds_image in backgrounds_images:
        for objects_image in objects_images:
            if object_larger_than_background(objects_image, backgrounds_image):
                return True
    return False


def load_backgrounds_images(req_backgrounds):
    backgrounds = []

    for req_background in req_backgrounds:
        image = get_cv2_background_by_path(req_background.image_path)
        backgrounds.append(image)

    return backgrounds


