from sly_globals import *

import cv2
import copy
import random
import augmentations

from sly_warnings import window_warner

import imgaug.augmenters as iaa

from functions_background import object_larger_than_background


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
    geometry = geometry.convert(sly.Bitmap)[0]

    crop_coords = get_crop_coords(geometry)
    cropped_image = crop_image_as_rectangle(image_as_arr, crop_coords)
    mask_matrix = geometry.data

    # cv2.imshow('cropped', cropped_image)
    # cv2.waitKey()
    # cropped_with_alpha = to_transparent_background(mask_matrix, cropped_image)
    # cv2.imwrite(f'transparent_{label.obj_class.name}.png', cropped_with_alpha)  # для отладки
    return cropped_image, mask_matrix


def reduce_object_size(curr_object):
    transformation = iaa.Resize(0.5, interpolation='cubic')
    augmentations.transform_object(curr_object, transformation, True)


def generate_base_primitives(extracted_objects, req_counts, curr_background, base_transform=None, can_resize=False,
                             sly_progress=None):
    temp_objects = []

    req_counts = {key: value for key, value in req_counts.items() if value > 0}

    if sly_progress:
        sly_progress.refresh_params('Generating base primitives', int(len(req_counts.keys())))

    for label, count in req_counts.items():

        curr_label_count = 0
        while curr_label_count < count:
            temp_extracted_objects = copy.deepcopy(extracted_objects)
            random.shuffle(temp_extracted_objects)

            for extracted_object in temp_extracted_objects:
                if extracted_object.class_name == label:
                    for tries in range(10):
                        if base_transform:
                            augmentations.transform_object(extracted_object, base_transform, True)

                        if not object_larger_than_background(extracted_object.image, curr_background):
                            break

                        if can_resize:
                            reduce_object_size(extracted_object)

                        if not object_larger_than_background(extracted_object.image, curr_background):
                            break

                    else:
                        window_warner('Selected Base augmentations enlarge objects too much, '
                                      'they start to exceed the size of the backgrounds. '
                                      'Please reselect Base augmentations.',
                                      fields=[{"field": "state.previewLoading", "payload": False},
                                              {"field": "data.videoUrl", "payload": None}])
                        return []

                    temp_objects.append(extracted_object)
                    curr_label_count += 1

                if curr_label_count == count:
                    break
        if sly_progress:
            sly_progress.next_step()

    return temp_objects


def get_objects_list_for_project(req_objects, sly_progress):
    """
    Extract all needed objects from images
    :param req_objects: list of required objects with obj_bitmaps and images_paths
    :return: list of extracted objects in ExtractedObject class format
    """
    extracted_objects = []

    if sly_progress:
        sly_progress.refresh_params(f"Extracting objects from images", len(req_objects))

    for curr_object in req_objects:
        ann = sly.Annotation.from_json(curr_object.annotation,
                                       project_meta)


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

        if sly_progress:
            sly_progress.next_step()

    if sly_progress:
        sly_progress.reset_params()

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


def load_objects_images(req_objects):
    objects_images = []

    extracted_objects = get_objects_list_for_project(req_objects)

    for extracted_object in extracted_objects:
        objects_images.append(extracted_object.image)

    return objects_images


def generate_object_counts(min_count, max_count):
    object_counts = {}
    while sum(object_counts.values()) == 0:
        for label, min_value in min_count.items():
            object_counts[label] = random.randint(min_value, max_count[label])
    #
    # if sum(object_counts.values()) == 0:
    #     generate_object_counts(min_count, max_count)

    return object_counts