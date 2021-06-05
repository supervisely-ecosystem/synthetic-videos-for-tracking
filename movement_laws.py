import numpy


class LinearLaw:
    """
    Закон линейного перемещения объекта.
    В качестве начальных параметров инициализируются:
    1. коэффициент угла наклона k
    2. смещение b
    """
    def __init__(self):
        self.k = numpy.random.uniform(0, 5)
        self.b = numpy.random.uniform(0, 10)

    def refresh_params(self):
        self.k = numpy.random.uniform(0, 10)
        self.b = numpy.random.uniform(0, 10)

    def calculator(self, x):
        return (self.k * x - self.k * (x - 1)) + self.b
