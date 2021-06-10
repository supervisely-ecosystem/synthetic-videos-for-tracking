from functions_background import *
from functions_objects import *
from functions_video import *

from functions_ann_keeper import AnnotationKeeper

from movement_laws import *
import imgaug.augmenters as iaa


class Scene:
    def __init__(self, width=1920, height=1080, object_transforms=None):
        self.width = width
        self.height = height
        self.backgrounds = []
        self.objects = []
        self.object_transforms = object_transforms

    def add_background(self, background_path):
        self.backgrounds.append(get_cv2_background_by_path(background_path))
        logger.info('background successfully added')

    def add_objects(self, project_path, dataset_name):
        extracted_objects = get_objects_list_for_project(project_path, dataset_name)
        self.objects.extend(extracted_objects)

        logger.info(f'[{len(extracted_objects)}] objects from {project_path}/{dataset_name} successfully added')
        logger.info(f'available objects:\n'
                    f'{get_available_objects(self.objects)}\n')

    def generate_video(self, video_name, fps, duration, objects_dict, movement_laws, self_overlay, speed_interval):
        temp_objects = load_required_objects(objects_dict, self.objects)
        initialize_controllers(temp_objects, movement_laws, speed_interval,
                                                               self_overlay, self.backgrounds[0].shape,
                               transforms=self.object_transforms)

        ann_keeper = AnnotationKeeper(self.backgrounds[0].shape, temp_objects)

        frames = generate_frames(fps, duration, self.backgrounds[0], temp_objects, ann_keeper)
        video_shape = (self.backgrounds[0].shape[1], self.backgrounds[0].shape[0])
        write_frames_to_file(video_name, fps, frames, video_shape)
        ann_keeper.upload_annotation()


project_path = './objects/lemons_annotated'
# project_path = './objects/small_squares'
dataset_name = 'ds1'


transform = iaa.Sequential([
    # iaa.Affine(rotate=(0, 0), scale=(0.5, 1)),
    # iaa.AdditiveGaussianNoise(scale=(10, 60)),
    # iaa.AddToHueAndSaturation((-60, 60)),  # HUE now isn't working, cause Alpha channel
    # iaa.ElasticTransformation(alpha=90, sigma=9),
])

custom_scene = Scene(object_transforms=transform)
custom_scene.add_background('./background_img/large_space.jpg')
# custom_scene.add_background('./background_img/white_test.jpg')
custom_scene.add_objects(project_path, dataset_name)
custom_scene.generate_video(video_name='./test1_random_walk_60fps.mp4',
                            duration=1,
                            fps=60,
                            objects_dict={'lemon': 6},
                            # objects_dict={'square': 4},
                            movement_laws=[{'law': RandomWalkingLaw, 'params': custom_scene.backgrounds[0].shape},
                                           {'law': LinearLaw, 'params': ()}],
                            self_overlay=0.4,
                            speed_interval=(1, 10))

