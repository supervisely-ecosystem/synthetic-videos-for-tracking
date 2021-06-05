from logger import logger

import cv2
import os


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


