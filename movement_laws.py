import numpy


class LinearLaw:
    def __init__(self):
        self.k = numpy.random.uniform(0, 10)
        self.b = numpy.random.uniform(0, 10)

        self.down = True

        self.refresh_params()

    def refresh_params(self):
        if self.down:

            self.down = False
        else:
            self.k = numpy.random.uniform(-10, 0)
            self.down = True

    def calculator(self, x):
        return (self.k * x - self.k * (x - 1)) + self.b
