from movement_laws import *
import numpy


class MovementController:
    def __init__(self, movement_law, speed_interval):
        self.x = 0
        self.y = 0
        self.movement_law = movement_law
        self.speed_interval = speed_interval

    def next_step(self):
        size_of_next_step = numpy.random.randint(self.speed_interval)
        self.x = self.x + size_of_next_step
        self.y = self.movement_law.calculator(self.x)
        return self.x, self.y

    def change_direction(self):
        pass
