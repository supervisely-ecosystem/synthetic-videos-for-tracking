from movement_laws import *
import numpy


def calculate_mask_area(**kwargs):
    areas = []
    for mask in kwargs.values():
        areas.append(sum([sum(row) for row in mask]))
    return areas


def calculate_intersection(mask_under, mask_over):
    return numpy.logical_and(mask_over.astype(bool), mask_under.astype(bool))


def resize_mask(base_shape, mask_coords, mask):
    base_matrix = numpy.zeros(base_shape)
    base_matrix[mask_coords[0]: mask_coords[0] + mask.shape[0],
                mask_coords[1]: mask_coords[1] + mask.shape[1]] = mask
    return base_matrix


def calculate_base_coords(added_coords, new_coords, lt=True):
    if lt:
        x = min(added_coords[0], new_coords[0])
        y = min(added_coords[1], new_coords[1])

    else:
        x = max(added_coords[0], new_coords[0])
        y = max(added_coords[1], new_coords[1])

    return x, y


def compare_overlays(added_object, curr_object, new_coords):
    added_mask = added_object.mask
    curr_mask = curr_object.mask

    x_min, y_min = calculate_base_coords(added_coords=(added_object.controller.x, added_object.controller.y),
                                         new_coords=new_coords,
                                         lt=True)
    x_max, y_max = calculate_base_coords(added_coords=(added_object.controller.x + added_mask.shape[0],
                                                       added_object.controller.y + added_mask.shape[1]),
                                         new_coords=(new_coords[0] + curr_mask.shape[0],
                                                     new_coords[1] + curr_mask.shape[1]),
                                         lt=False)

    added_x, added_y = added_object.controller.x - x_min, added_object.controller.y - y_min
    curr_x, curr_y = new_coords[0] - x_min, new_coords[1] - y_min

    added_rebased_mask = resize_mask(base_shape=(x_max, y_max),
                                     mask_coords=(added_x, added_y),
                                     mask=added_mask)

    curr_rebased_mask = resize_mask(base_shape=(x_max, y_max),
                                    mask_coords=(curr_x, curr_y),
                                    mask=curr_mask)

    intersected_mask = calculate_intersection(added_rebased_mask, curr_rebased_mask).astype(int)
    intersection_area, added_area = calculate_mask_area(inter_mask=intersected_mask,
                                                        added_mask=added_mask)

    if intersected_mask / added_area > added_object.controller.self_overlay:
        return False
    return True



class MovementController:
    """
    Класс позволяет контроллировать расположение объекта на сцене
    """

    def __init__(self, movement_law, speed_interval, self_overlay, x_high_limit, y_high_limit, x_low_limit=0,
                 y_low_limit=0):
        self.x = numpy.random.randint(x_low_limit, x_high_limit)
        self.y = numpy.random.randint(y_low_limit, y_high_limit)
        self.movement_law = movement_law
        self.speed_interval = speed_interval
        self.self_overlay = self_overlay

        self.x_high_limit = x_high_limit
        self.y_high_limit = y_high_limit
        self.x_low_limit = x_low_limit
        self.y_low_limit = y_low_limit

        self.down = 1
        self.right = 1

    def generate_new_coords(self):
        """
        Генерирует следующий шаг координат
        :return: координаты объекта
        """
        size_of_next_step = int(numpy.random.randint(self.speed_interval[0], self.speed_interval[1]))
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
        x, y = self.generate_new_coords()

        if not self.check_bounding_coords_availability((x, y)):
            x, y = self.generate_new_coords()

        if not self.check_overlay_coords_availability((x, y), added_objects, curr_object):
            x, y = self.generate_new_coords()

        self.x, self.y = x, y
        return self.x, self.y

    def check_overlay_coords_availability(self, new_coords, added_objects, curr_object):
        """Проверка доступности по координат"""
        for added_object in added_objects:
            if compare_overlays(added_object, curr_object, new_coords):
                return False


    def check_bounding_coords_availability(self, new_coords):
        changed = False
        if not self.check_x_availability(new_coords[0]):
            self.change_x_direction()

        if not self.check_y_availability(new_coords[1]):
            self.change_y_direction()

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
