import supervisely_lib as sly
import numpy
import cv2
import os

from logger import logger


class ExtractedObject:
    """
    Класс извлеченного объекта.
    Содержит базовые характеристики, необходимые для работы с объектом.
    """
    def __init__(self, image, mask, area, class_name, proj_path, ds_name):
        self.image = image
        self.image_backup = image
        self.mask = mask
        self.mask_backup = mask
        self.area = area
        self.class_name = class_name
        self.proj_path = proj_path
        self.ds_name = ds_name


def open_project(proj_path):
    """
    Открвыает проект в формата SLY
    :param proj_path: путь до проекта
    :return: объект проекта
    """
    return sly.Project(proj_path, sly.OpenMode.READ)


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

    return sly.Rectangle(x, y, x + len(geometry.data) - 1, y + len(geometry.data[0]) - 1)


def crop_image_as_rectangle(src_image, crop_coords):
    """
    Обрезает по прямоугольнику конкертный объект
    :param src_image: исходное изображение
    :param crop_coords: координаты BB объекта
    :return: вырезанная область
    """
    return sly.imaging.image.crop(src_image, crop_coords)


def get_three_channel_mask(mask):
    """
    Трансформирует маску из однокаланьной в трехканальную
    используется для удаления фона
    :param mask: одноканальная маска
    :return: трехканальная маска
    """
    three_channel_mask = []

    for row in mask:
        temp_row = []
        for curr_value in row:
            temp_row.append([curr_value, curr_value, curr_value])

        three_channel_mask.append(temp_row)

    return numpy.asarray(three_channel_mask)


def to_transparent_background(mask, cropped_image):
    """
    Устанавливает интенсивность пикселей по маске 0,
    итогом служит прозрачный фон
    :param mask: маска объекта
    :param cropped_image: обрезанный объект
    :return: обрезанный объект с альфа
    """
    cropped_with_alpha = cv2.cvtColor(cropped_image, cv2.COLOR_RGBA2BGRA)
    three_channel_mask = get_three_channel_mask(mask)
    bg_mask = numpy.invert(three_channel_mask)

    alpha = cropped_with_alpha[:, :, 3]
    alpha[numpy.all(bg_mask, 2)] = 0
    return cropped_with_alpha


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

    # cropped_with_alpha = to_transparent_background(mask_matrix, cropped_image)
    # cv2.imwrite(f'transparent_{label.obj_class.name}.png', cropped_with_alpha)  # для отладки
    return cropped_image, mask_matrix


def get_objects_list_for_project(project_path, dataset_name):
    """
    Извлекает все объекты для проекта, хранит в виде объектов класса ExtractedObject
    :param project_path: путь до проекта формата SLY
    :param dataset_name: имя датасета
    :return: список объектов, извлеченных из проекта в виде объектов класса ExtractedObject
    """
    extracted_objects = []

    project = open_project(project_path)
    images_names = get_images_names(os.path.join(project_path, dataset_name))
    logger.info(f'extracting objects...')
    for image_name in images_names:  # по всем изображениям в датасете
        item_paths = project.datasets.get(dataset_name).get_item_paths(image_name)
        ann = sly.Annotation.load_json_file(item_paths.ann_path, project.meta)

        image_as_arr = cv2.imread(item_paths.img_path)
        # image_as_arr = cv2.cvtColor(image_as_arr, cv2.COLOR_BGR2RGB)

        for label in ann.labels:  # по всем объектам на изображении
            # print(f'workin now with {label.obj_class.name}')  #  для отладки
            # logger.info(f'[{len(extracted_objects)}] extracting {label.obj_class.name} now')
            extracted_object_image, mask = extract_object_from_image(image_as_arr, label)

            extracted_objects.append(
                ExtractedObject(image=extracted_object_image,
                                mask=mask,
                                area=label.area,
                                class_name=label.obj_class.name,
                                proj_path=project_path,
                                ds_name=dataset_name)
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

