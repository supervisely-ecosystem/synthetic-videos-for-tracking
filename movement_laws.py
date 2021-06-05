import numpy


class LinearLaw:
    def __init__(self):
        self.k = 0
        self.b = 0

        self.down = False

        self.refresh_params()

    def refresh_params(self):
        if self.down:
            self.k = numpy.random.uniform(0, 10)
            self.down = False
        else:
            self.k = numpy.random.uniform(-10, 0)
            self.down = True
        self.b = numpy.random.uniform(-20, 20)

    def calculator(self, x):
        return self.k * x + self.b
