import supervisely_lib as sly
import numpy
import cv2
import os

from sly_globals import *

from logger import logger


class ExtractedObject:
    """
    Класс извлеченного объекта.
    Содержит базовые характеристики, необходимые для работы с объектом.
    """
    def __init__(self, image, mask, is_tracking, area, class_name, image_id, ds_id, sly_ann):
        self.image = image
        self.image_backup = image
        self.mask = mask
        self.mask_backup = mask
        self.is_tracking = is_tracking
        self.area = area
        self.class_name = class_name
        self.image_id = image_id
        self.ds_id = ds_id

        self.sly_ann = sly_ann


def get_images_names(path_to_ds):
    """
    Возвращает список имен изображений проекта, которые лежат в img
    :param path_to_ds: путь до директории датасета
    :return: список имен изображений
    """
    return os.listdir(os.path.join(path_to_ds, 'img/'))


def get_crop_coords(geometry):
    """
    Возвращает BB объекта
    :param geometry: Bitmap объекта
    :return: BB объекта
    """
    x = geometry.origin.row
    y = geometry.origin.col

    return sly.Rectangle(x, y, x + geometry.data.shape[0] - 1, y + geometry.data.shape[1] - 1)


def crop_image_as_rectangle(src_image, crop_coords):
    """
    Обрезает по прямоугольнику конкертный объект
    :param src_image: исходное изображение
    :param crop_coords: координаты BB объекта
    :return: вырезанная область
    """
    return sly.imaging.image.crop(src_image, crop_coords)


def extract_object_from_image(image_as_arr, label):
    """
    Функция извлекает объект из изображения
    :param image_as_arr: исходное изображение в формате numpy
    :param label: информация об объекте
    :return: вырезанный объект, маска объекта
    """
    geometry = label.geometry

    crop_coords = get_crop_coords(geometry)
    cropped_image = crop_image_as_rectangle(image_as_arr, crop_coords)
    mask_matrix = geometry.data

    # cv2.imshow('cropped', cropped_image)
    # cv2.waitKey()
    # cropped_with_alpha = to_transparent_background(mask_matrix, cropped_image)
    # cv2.imwrite(f'transparent_{label.obj_class.name}.png', cropped_with_alpha)  # для отладки
    return cropped_image, mask_matrix


def generate_needed_objects(extracted_objects, req_counts, base_transform=None):
    temp_objects = []
    for label, count in req_counts.items():
        if count > 0:
            curr_label_count = 0
            while curr_label_count != count:
                for extracted_object in extracted_objects:
                    if extracted_object.class_name == label:
                        temp_objects.append(extracted_object)
                        curr_label_count += 1






def get_objects_list_for_project(req_objects):
    """
    Extract all needed objects from images
    :param req_objects: list of required objects with obj_bitmaps and images_paths
    :return: list of extracted objects in ExtractedObject class format
    """
    extracted_objects = []

    for curr_object in req_objects:
        ann = sly.Annotation.from_json(curr_object.annotation,
                                       sly.ProjectMeta.from_json(api.project.get_meta(id=project_id)))

        image_as_arr = cv2.imread(curr_object.image_path)
        for label in ann.labels:  # по всем объектам на изображении
            extracted_object_image, mask = extract_object_from_image(image_as_arr, label)

            extracted_objects.append(
                ExtractedObject(image=extracted_object_image,
                                mask=mask,
                                is_tracking=curr_object.is_tracking,
                                area=label.area,
                                class_name=label.obj_class.name,
                                image_id=curr_object.image_id,
                                ds_id=curr_object.ds_id,
                                sly_ann=ann)
            )

    return extracted_objects


def get_available_objects(objects):
    """
    Возвращает список названий классов извлеченных объектов
    :param objects: список извлеченных объектов
    :return: словрь названий классов извлеченных объектов {название: количество}
    """
    obj_names = {}
    for curr_object in objects:
        curr_num = obj_names.get(curr_object.class_name, 0)
        obj_names[curr_object.class_name] = curr_num + 1
    return obj_names


def generate_base_primitives(extracted_objects, required_objects):

    return 0
