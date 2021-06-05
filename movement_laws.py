import numpy


class LinearLaw:
    def __init__(self):
        self.k = 0
        self.b = 0

        self.refresh_params()

    def refresh_params(self):
        self.k = numpy.random.uniform(-10, 10)
        self.b = numpy.random.uniform(-20, 20)

    def calculator(self, x):
        return self.k * x + self.b
