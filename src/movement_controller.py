from movement_laws import *
import numpy
from collections import namedtuple
from imgaug.augmentables.segmaps import SegmentationMapsOnImage
from logger import logger
import cv2

from augmentations import *


from time import time


class MovementController:
    """
    Класс позволяет контроллировать расположение объекта на сцене
    """

    def __init__(self, curr_object, movement_law, speed_interval, self_overlay, background_shape,
                 general_transforms=None, minor_transforms=None):

        self.movement_law = movement_law
        self.speed_interval = speed_interval
        self.self_overlay = numpy.random.uniform(self_overlay[0], self_overlay[1])
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

    def transform_object(self, curr_object, is_general_transform=False):

        if is_general_transform:
            transform_object(curr_object, self.general_transforms, is_general_transform)

        else:
            transform_object(curr_object, self.minor_transforms, is_general_transform)

        self.calculate_allowable_limits(curr_object.image)

        return 0

    def next_step(self, added_objects, curr_object):
        """
        Рассчитывает следующий шаг.
        Если объект не может попасть на следующий шаг — производит перерассчет
        :return: новые координаты объекта
        """

        if self.minor_transforms:
            self.transform_object(curr_object, is_general_transform=False)

        size_of_next_step = self.size_of_next_step

        x, y = self.generate_new_coords(size_of_next_step)

        collision_solver = 1
        while not self.check_overlay_coords_availability((x, y), added_objects, curr_object):
            x, y = self.generate_new_coords(size_of_next_step * collision_solver)
            while not self.check_bounding_coords_availability((x, y), curr_object):
                x, y = curr_object.controller.x, curr_object.controller.y

            collision_solver *= 1.3

            if collision_solver > 50:
                return -1  # collision problem

        while not self.check_bounding_coords_availability((x, y), curr_object):
            x, y = curr_object.controller.x, curr_object.controller.y

        self.x, self.y = x, y
        return 0

    def check_overlay_coords_availability(self, new_coords, added_objects, curr_object):
        """Проверка доступности по координат"""
        for added_object in added_objects:
            if not compare_overlays_by_rectangles(added_object, curr_object, new_coords):

                self.change_x_direction()
                self.change_y_direction()

                added_object.controller.right = self.right * -1
                added_object.controller.down = self.down * -1

                self.size_of_next_step = int(numpy.random.randint(self.speed_interval[0], self.speed_interval[1]))
                added_object.controller.movement_law.refresh_params()
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


def area(a, b):  # returns None if rectangles don't intersect
    dx = min(a.xmax, b.xmax) - max(a.xmin, b.xmin)
    dy = min(a.ymax, b.ymax) - max(a.ymin, b.ymin)
    if (dx >= 0) and (dy >= 0):
        return dx * dy


def compare_overlays_by_rectangles(added_object, curr_object, new_coords):
    added_mask_shape = added_object.image.shape
    curr_mask_shape = curr_object.image.shape

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


def find_mask_tight_bbox(raw_mask: numpy.ndarray):
    rows = list(numpy.any(raw_mask, axis=1).tolist())
    cols = list(numpy.any(raw_mask, axis=0).tolist())
    top_margin = rows.index(True)
    bottom_margin = rows[::-1].index(True)
    left_margin = cols.index(True)
    right_margin = cols[::-1].index(True)
    return top_margin, left_margin, \
           len(rows) - bottom_margin, len(cols) - right_margin