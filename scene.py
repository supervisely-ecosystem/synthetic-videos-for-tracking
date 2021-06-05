from logger import logger

from functions_background import *
from functions_objects import *


class Scene:
    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height
        self.background = []
        self.objects = []

    def add_background(self, background_path):
        self.background.append(get_cv2_background_by_path(background_path))
        logger.info('background successfully added')

    def add_objects(self, project_path, dataset_name):
        extracted_objects = get_objects_list_for_project(project_path, dataset_name)
        self.objects.extend(extracted_objects)
        logger.info(f'[{len(extracted_objects)}] objects from {project_path}/{dataset_name} successfully added')




project_path = './objects/lemons_annotated'
dataset_name = 'ds1'

custom_scene = Scene()
custom_scene.add_background('./background_img/space.jpg')
custom_scene.add_objects(project_path, dataset_name)



input()
