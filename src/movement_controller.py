from movement_laws import *
import numpy
from collections import namedtuple
from logger import logger


def area(a, b):  # returns None if rectangles don't intersect
    dx = min(a.xmax, b.xmax) - max(a.xmin, b.xmin)
    dy = min(a.ymax, b.ymax) - max(a.ymin, b.ymin)
    if (dx >= 0) and (dy >= 0):
        return dx * dy


def calculate_base_coords(added_coords, new_coords, lt=True):
    if lt:
        x = min(added_coords[0], new_coords[0])
        y = min(added_coords[1], new_coords[1])

    else:
        x = max(added_coords[0], new_coords[0])
        y = max(added_coords[1], new_coords[1])

    return x, y


def compare_overlays_by_rectangles(added_object, curr_object, new_coords):
    added_mask_shape = added_object.mask.shape
    curr_mask_shape = curr_object.mask.shape

    # intersected_mask = calculate_intersection(added_rebased_mask, curr_rebased_mask).astype(int)
    # intersection_area, added_area = calculate_mask_area(inter_mask=intersected_mask,
    #                                                     added_mask=added_mask)

    added_area = added_mask_shape[0] * added_mask_shape[1]

    Rectangle = namedtuple('Rectangle', 'xmin ymin xmax ymax')

    ra = Rectangle(added_object.controller.x,
                   added_object.controller.y,
                   added_object.controller.x + added_mask_shape[0],
                   added_object.controller.y + added_mask_shape[1])
    rb = Rectangle(
        new_coords[0],
        new_coords[1],
        new_coords[0] + curr_mask_shape[0],
        new_coords[1] + curr_mask_shape[1]
    )

    intersection_area = area(ra, rb)

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

    def __init__(self, movement_law, speed_interval, self_overlay, x_high_limit, y_high_limit, x_low_limit=0,
                 y_low_limit=0, transforms=None):
        self.x = numpy.random.randint(x_low_limit, x_high_limit)
        self.y = numpy.random.randint(y_low_limit, y_high_limit)
        self.movement_law = movement_law
        self.speed_interval = speed_interval
        self.self_overlay = self_overlay
        self.size_of_next_step = int(numpy.random.randint(self.speed_interval[0], self.speed_interval[1]))

        self.x_high_limit = x_high_limit
        self.y_high_limit = y_high_limit
        self.x_low_limit = x_low_limit
        self.y_low_limit = y_low_limit

        self.down = 1
        self.right = 1

        self.transforms = transforms

    def generate_new_coords(self, size_of_next_step):
        """
        Генерирует следующий шаг координат
        :return: координаты объекта
        """

        x = self.x + size_of_next_step * self.right
        y_div = self.movement_law.calculator(x)
        y = self.y + y_div * self.down
        return int(x), int(y)

    def next_step(self, added_objects, curr_object):
        """
        Рассчитывает следующий шаг.
        Если объект не может попасть на следующий шаг — производит перерассчет
        :return: новые координаты объекта
        """
        if self.transforms:

            curr_object.image = self.transforms(image=curr_object.image_backup)
            # curr_object.image, curr_object.mask = self.transforms(image=curr_object.image_backup,
                                                                  # segmentation_maps=curr_object.mask_backup)

        size_of_next_step = self.size_of_next_step

        x, y = self.generate_new_coords(size_of_next_step)

        collision_solver = 1
        while not self.check_overlay_coords_availability((x, y), added_objects, curr_object):

            x, y = self.generate_new_coords(size_of_next_step * collision_solver)
            collision_solver *= 1.1

        outbound_solver = 1
        while not self.check_bounding_coords_availability((x, y)):
            x, y = self.generate_new_coords(size_of_next_step * outbound_solver)
            outbound_solver *= 1.1

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

    def check_bounding_coords_availability(self, new_coords):
        changed = False
        if not self.check_x_availability(new_coords[0]):
            self.change_x_direction()
            changed = True

        if not self.check_y_availability(new_coords[1]):
            self.change_y_direction()
            changed = True

        if changed:
            return False
        return True

    def check_y_availability(self, new_y):
        if new_y > self.y_high_limit or new_y < self.y_low_limit:
            return False
        else:
            return True

    def check_x_availability(self, new_x):
        """Проверка доступности по X"""
        if new_x > self.x_high_limit or new_x < self.x_low_limit:
            return False
        else:
            return True

    def change_y_direction(self):
        """Изменить направление по Y"""
        self.down = self.down * -1

    def change_x_direction(self):
        """Изменить направление по X"""
        self.right = self.right * -1