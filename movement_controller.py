from movement_laws import *
import numpy


class MovementController:
    def __init__(self, movement_law, speed_interval, x_limit, y_limit):
        self.x = 0
        self.y = 0
        self.movement_law = movement_law
        self.speed_interval = speed_interval

        self.x_limit = x_limit
        self.y_limit = y_limit


    def generate_new_coords(self):
        size_of_next_step = int(numpy.random.randint(self.speed_interval[0], self.speed_interval[1]))
        x = self.x + size_of_next_step
        y = self.movement_law.calculator(x)
        return x, y


    def next_step(self):
        x, y = self.generate_new_coords()
        while not self.check_coords_availability(x, y):
            self.change_direction()
            x, y = self.generate_new_coords()

        self.x, self.y = int(x), int(y)
        return self.x, self.y

    def check_coords_availability(self, x, y):
        if x > self.x_limit or y > self.y_limit or x < 0 or y < 0:
            return False
        else:
            return True

    def change_direction(self):
        self.movement_law.refresh_params()
