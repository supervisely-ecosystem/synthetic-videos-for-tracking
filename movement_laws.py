import numpy


class LinearLaw:
    def __init__(self):
        self.k = numpy.random.uniform(0, 10)
        self.b = numpy.random.uniform(0, 10)

    def refresh_params(self):
        self.k = numpy.random.uniform(0, 10)
        self.b = numpy.random.uniform(0, 10)

    def calculator(self, x):
        return (self.k * x - self.k * (x - 1)) + self.b
