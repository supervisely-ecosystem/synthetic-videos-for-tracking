import numpy
from scipy.interpolate import interp1d


class LinearLaw:
    """
    Закон линейного перемещения объекта.
    В качестве начальных параметров инициализируются:
    1. коэффициент угла наклона k
    2. смещение b
    """
    def __init__(self):
        self.k = numpy.random.uniform(0, 2)
        self.b = numpy.random.uniform(0, 10)

    def refresh_params(self):
        self.k = numpy.random.uniform(0, 3)
        # self.b = numpy.random.uniform(0, 10)

    def calculator(self, x):
        return (self.k * x - self.k * (x - 1)) + self.b


class RandomWalkingLaw:
    def __init__(self, x_high_limit, y_high_limit, x_low_limit=0,
                 y_low_limit=0):

        self.x_high_limit = x_high_limit * 4
        self.y_high_limit = y_high_limit + y_high_limit
        self.x_low_limit = x_low_limit - x_high_limit
        self.y_low_limit = y_low_limit - y_low_limit

        self.x = numpy.linspace(self.x_low_limit, self.x_high_limit, num=60, endpoint=True)

        self.y = numpy.random.randint(low=self.y_low_limit, high=self.y_high_limit, size=(len(self.x),))
        self.f = interp1d(self.x, self.y, kind='cubic')

    def refresh_params(self):
        self.x = sorted(list(set(numpy.random.randint(low=self.x_low_limit, high=self.x_high_limit, size=(30,)))))
        self.y = (numpy.random.randint(low=self.y_low_limit, high=self.y_high_limit, size=(len(self.x),)))

        self.f = interp1d(self.x, self.y, kind='linear')

    def calculator(self, x):
        return abs(self.f(x) - self.f(x - 1))


