from functions_background import *
from functions_objects import *
from functions_video import *

from movement_laws import *


class Scene:
    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height
        self.backgrounds = []
        self.objects = []

    def add_background(self, background_path):
        self.backgrounds.append(get_cv2_background_by_path(background_path))
        logger.info('background successfully added')

    def add_objects(self, project_path, dataset_name):
        extracted_objects = get_objects_list_for_project(project_path, dataset_name)
        self.objects.extend(extracted_objects)

        logger.info(f'[{len(extracted_objects)}] objects from {project_path}/{dataset_name} successfully added')
        logger.info(f'available objects:\n'
                    f'{get_available_objects(self.objects)}\n')

    def generate_video(self, video_name, fps, duration, objects_dict, movement_law, speed_interval):
        temp_objects = load_required_objects(objects_dict, self.objects)
        frames = generate_frames(fps, duration, self.backgrounds[0], temp_objects, movement_law, speed_interval)
        video_shape = (self.backgrounds[0].shape[1], self.backgrounds[0].shape[0])
        write_frames_to_file(video_name, fps, frames, video_shape)


project_path = './objects/lemons_annotated'
dataset_name = 'ds1'

custom_scene = Scene()
custom_scene.add_background('./background_img/space.jpg')
custom_scene.add_objects(project_path, dataset_name)
custom_scene.generate_video(video_name='./test1_60fps.mp4',
                            duration=10,
                            fps=60,
                            objects_dict={'lemon': 2, 'kiwi': 2},
                            movement_law=LinearLaw,
                            speed_interval=(1, 30))

