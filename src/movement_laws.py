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
        self.y_muffler = numpy.random.uniform(1, 10)

    def refresh_params(self):
        self.k = numpy.random.uniform(0, 3)
        self.y_muffler = numpy.random.uniform(1, 10)
        # self.b = numpy.random.uniform(0, 10)

    def calculator(self, x):
        return ((self.k * x - self.k * (x - 1)) + self.b) / self.y_muffler


class RandomWalkingLaw:
    def __init__(self, x_high_limit, y_high_limit, x_low_limit=0,
                 y_low_limit=0):

        self.x_high_limit = x_high_limit * 4
        self.y_high_limit = y_high_limit + y_high_limit
        self.x_low_limit = x_low_limit - x_high_limit
        self.y_low_limit = y_low_limit - y_low_limit

        self.x = numpy.linspace(self.x_low_limit, self.x_high_limit, num=60, endpoint=True)

        self.y = numpy.random.randint(low=self.y_low_limit, high=self.y_high_limit, size=(len(self.x),))
        self.f = interp1d(self.x, self.y, kind='cubic', fill_value='extrapolate')

        self.y_muffler = numpy.random.uniform(1, 10)

    def refresh_params(self):
        self.x = numpy.linspace(self.x_low_limit, self.x_high_limit, num=60, endpoint=True)

        self.y = numpy.random.randint(low=self.y_low_limit, high=self.y_high_limit, size=(len(self.x),))
        self.f = interp1d(self.x, self.y, kind='cubic', fill_value='extrapolate')

        self.y_muffler = numpy.random.uniform(1, 10)

    def calculator(self, x):
        return abs(self.f(x) - self.f(x - 1)) / self.y_muffler


def load_movements_laws(custom_scene, req_laws):
    chosen_laws = []

    laws = {
        'linearLaw': {'law': RandomWalkingLaw, 'params': custom_scene.backgrounds[0].shape},
        'randomLaw': {'law': LinearLaw, 'params': ()},
    }

    for law_name, law_status in req_laws.items():
        if law_status:
            chosen_laws.append(laws[law_name])

    return chosen_laws


