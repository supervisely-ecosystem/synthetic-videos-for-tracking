from movement_laws import *
import numpy
from collections import namedtuple
from imgaug.augmentables.segmaps import SegmentationMapsOnImage
from logger import logger
import cv2

from functions_objects import get_three_channel_mask, to_transparent_background
from time import time

def area(a, b):  # returns None if rectangles don't intersect
    dx = min(a.xmax, b.xmax) - max(a.xmin, b.xmin)
    dy = min(a.ymax, b.ymax) - max(a.ymin, b.ymin)
    if (dx >= 0) and (dy >= 0):
        return dx * dy

#
# def calculate_base_coords(added_coords, new_coords, lt=True):
#     if lt:
#         x = min(added_coords[0], new_coords[0])
#         y = min(added_coords[1], new_coords[1])
#
#     else:
#         x = max(added_coords[0], new_coords[0])
#         y = max(added_coords[1], new_coords[1])
#
#     return x, y


def compare_overlays_by_rectangles(added_object, curr_object, new_coords):
    added_mask_shape = added_object.image.shape
    curr_mask_shape = curr_object.image.shape

    # intersected_mask = calculate_intersection(added_rebased_mask, curr_rebased_mask).astype(int)
    # intersection_area, added_area = calculate_mask_area(inter_mask=intersected_mask,
    #                                                     added_mask=added_mask)

    added_area = added_mask_shape[0] * added_mask_shape[1]

    Rectangle = namedtuple('Rectangle', 'xmin ymin xmax ymax')

    ra = Rectangle(added_object.controller.x,
                   added_object.controller.y,
                   added_object.controller.x + added_mask_shape[1],
                   added_object.controller.y + added_mask_shape[0])
    rb = Rectangle(
        new_coords[0],
        new_coords[1],
        new_coords[0] + curr_mask_shape[1],
        new_coords[1] + curr_mask_shape[0]
    )

    intersection_area = area(ra, rb)
    # print(intersection_area)

    if intersection_area:
        # logger.debug(f'\nlower object area {added_area}\n'
        #              f'intersection object area {intersection_area}\n')
        if (intersection_area / added_area) > added_object.controller.self_overlay:

            return False
    return True


class MovementController:
    """
    Класс позволяет контроллировать расположение объекта на сцене
    """

    def __init__(self, curr_object, movement_law, speed_interval, self_overlay, background_shape,
                 general_transforms=None, minor_transforms=None):

        self.movement_law = movement_law
        self.speed_interval = speed_interval
        self.self_overlay = self_overlay
        self.size_of_next_step = int(numpy.random.randint(self.speed_interval[0], self.speed_interval[1]))

        self.background_shape = background_shape

        self.x_high_limit = 0
        self.y_high_limit = 0
        self.x_low_limit = 0
        self.y_low_limit = 0

        self.calculate_allowable_limits(curr_object.image)

        self.x = numpy.random.randint(self.x_low_limit, self.x_high_limit)
        self.y = numpy.random.randint(self.y_low_limit, self.y_high_limit)

        self.down = 1
        self.right = 1

        self.general_transforms = general_transforms  # applied on limits and collisions
        self.minor_transforms = minor_transforms  # applied on every step

    def calculate_allowable_limits(self, object_image):
        image_shape = object_image.shape

        self.x_high_limit = self.background_shape[1] - image_shape[1]
        self.y_high_limit = self.background_shape[0] - image_shape[0]
        self.x_low_limit = 0
        self.y_low_limit = 0


    def generate_new_coords(self, size_of_next_step):
        """
        Генерирует следующий шаг координат
        :return: координаты объекта
        """

        x = self.x + size_of_next_step * self.right
        y_div = self.movement_law.calculator(x)
        y = self.y + y_div * size_of_next_step * self.down
        return int(x), int(y)

    def transform_object(self, curr_object, general_transform=False):

        segment_map = SegmentationMapsOnImage(curr_object.mask, shape=curr_object.mask.shape)
        if general_transform:
            image_aug, segment_map_aug = self.general_transforms(image=curr_object.image_backup,
                                                                 segmentation_maps=segment_map)
            mask_aug = segment_map_aug.get_arr()

            if not ((image_aug.shape[0] < 350 or image_aug.shape[1] < 350) or
                    (image_aug.shape[0] > 800 or image_aug.shape[1] > 800)):
                curr_object.image = image_aug
                curr_object.image_backup = image_aug
                curr_object.mask = mask_aug

                self.calculate_allowable_limits(curr_object.image)

        else:
            stat_time = time()
            # logger.info('-' * 80)
            # logger.info(f'to rgba: {time() - stat_time}')

            image_aug, segment_map_aug = self.minor_transforms(image=curr_object.image_backup,
                                                               segmentation_maps=segment_map)

            # logger.info(f'trans: {time() - stat_time}')
            mask_aug = segment_map_aug.get_arr()
            # logger.info(f'mask aug: {time() - stat_time}')
            # logger.info(f'tchm: {time() - stat_time}')

            # logger.info(f'invert: {time() - stat_time}')


            # logger.info(f'rgba: {time() - stat_time}')

            # logger.info(f'alpha: {time() - stat_time}')
            curr_object.image = image_aug
            curr_object.mask = mask_aug
            # logger.info(f'done: {time() - stat_time}')
            # logger.info('-' * 80)

        return 0

    def next_step(self, added_objects, curr_object):
        """
        Рассчитывает следующий шаг.
        Если объект не может попасть на следующий шаг — производит перерассчет
        :return: новые координаты объекта
        """
        stat_time = time()

        is_general_transformed = False

        if self.minor_transforms:
            self.transform_object(curr_object, general_transform=False)

        # logger.info(f'minor_trans: {time() - stat_time}')
        stat_time = time()

        size_of_next_step = self.size_of_next_step

        x, y = self.generate_new_coords(size_of_next_step)

        collision_solver = 1
        while not self.check_overlay_coords_availability((x, y), added_objects, curr_object):

            if self.general_transforms and not is_general_transformed:
                self.transform_object(curr_object, general_transform=True)

                is_general_transformed = True
            if collision_solver > 1:
                print()

            x, y = self.generate_new_coords(size_of_next_step * collision_solver)

            collision_solver *= 1.01
        # logger.info(f'collision: {time() - stat_time}')
        stat_time = time()

        # outbound_solver = 1
        while not self.check_bounding_coords_availability((x, y), curr_object):
            if self.general_transforms and not is_general_transformed:
                self.transform_object(curr_object, general_transform=True)

                is_general_transformed = True
            x, y = curr_object.controller.x, curr_object.controller.y
            # x, y = self.generate_new_coords(size_of_next_step * outbound_solver)

        # logger.info(f'outbound: {time() - stat_time}')
        self.x, self.y = x, y
        return self.x, self.y

    def check_overlay_coords_availability(self, new_coords, added_objects, curr_object):
        """Проверка доступности по координат"""
        for added_object in added_objects:
            if not compare_overlays_by_rectangles(added_object, curr_object, new_coords):

                self.change_x_direction()
                self.change_y_direction()

                added_object.controller.right = self.right * -1
                added_object.controller.down = self.down * -1
                # added_object.controller.movement_law.refresh_params()
                # added_object.controller.generate_new_coords(added_object.controller.size_of_next_step)

                return False
        return True

    def check_bounding_coords_availability(self, new_coords, curr_object):
        changed = False
        if not self.check_and_fix_x_availability(new_coords[0], curr_object):
            self.change_x_direction()
            changed = True

        if not self.check_and_fix_y_availability(new_coords[1], curr_object):
            self.change_y_direction()
            changed = True

        if changed:
            return False
        return True

    def check_and_fix_y_availability(self, new_y, curr_object):
        if new_y > self.y_high_limit:
            curr_object.controller.y = self.y_high_limit
            return False
        elif new_y < self.y_low_limit:
            curr_object.controller.y = self.y_low_limit
            return False
        else:
            return True

    def check_and_fix_x_availability(self, new_x, curr_object):
        """Проверка доступности по X"""
        if new_x > self.x_high_limit:
            curr_object.controller.x = self.x_high_limit
            return False
        elif new_x < self.x_low_limit:
            curr_object.controller.x = self.x_low_limit
            return False
        else:
            return True

    def change_y_direction(self):
        """Изменить направление по Y"""
        self.down = self.down * -1

    def change_x_direction(self):
        """Изменить направление по X"""
        self.right = self.right * -1
