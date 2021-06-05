from movement_laws import *
import numpy


class MovementController:
    def __init__(self, movement_law, speed_interval, x_high_limit, y_high_limit, x_low_limit=0, y_low_limit=0):
        self.x = 0
        self.y = 0
        self.movement_law = movement_law
        self.speed_interval = speed_interval

        self.x_high_limit = x_high_limit
        self.y_high_limit = y_high_limit
        self.x_low_limit = x_low_limit
        self.y_low_limit = y_low_limit

        self.down = 1
        self.right = 1

    def generate_new_coords(self):
        size_of_next_step = int(numpy.random.randint(self.speed_interval[0], self.speed_interval[1]))
        x = self.x + size_of_next_step * self.right
        y_div = self.movement_law.calculator(x)
        y = self.y + y_div * self.down
        return x, y

    def next_step(self):
        x, y = self.generate_new_coords()

        if not self.check_y_availability(y):
            self.change_y_direction()
            x, y = self.generate_new_coords()

        if not self.check_x_availability(x):
            self.change_x_direction()
            x, y = self.generate_new_coords()

        self.x, self.y = int(x), int(y)
        return self.x, self.y

    def check_y_availability(self, y):
        if y > self.y_high_limit or y < self.y_low_limit:
            return False
        else:
            return True

    def check_x_availability(self, x):
        if x > self.x_high_limit or x < self.x_low_limit:
            return False
        else:
            return True

    def change_y_direction(self):
        self.down = self.down * -1

    def change_x_direction(self):
        self.right = self.right * -1

