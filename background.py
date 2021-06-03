from logger import logger

from functions import *


class Scene:
    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height
        self.background = []
        self.objects = []

    def add_background(self, background_path):
        self.background.append(get_cv2_background_by_path(background_path))

        logger.info('background successfully added')


custom_scene = Scene()
custom_scene.add_background('./background_img/space.jpg')

input()
