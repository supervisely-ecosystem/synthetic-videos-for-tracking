from functions_background import *
from functions_objects import *
from functions_video import *

from functions_ann_keeper import AnnotationKeeper

from movement_laws import *

import imgaug.augmenters as iaa

import numpy


class Scene:
    def __init__(self, width=1920, height=1080, object_general_transforms=None,
                 object_minor_transforms=None, frame_transform=None):
        self.width = width
        self.height = height
        self.backgrounds = []
        self.objects = []
        self.object_general_transforms = object_general_transforms
        self.object_minor_transforms = object_minor_transforms
        self.frame_transform = frame_transform

    def add_background(self, background_path):
        self.backgrounds.append(get_cv2_background_by_path(background_path))
        logger.info('background successfully added')

    def add_objects(self, project_path, dataset_name):
        extracted_objects = get_objects_list_for_project(project_path, dataset_name)
        self.objects.extend(extracted_objects)

        logger.info(f'[{len(extracted_objects)}] objects from {project_path}/{dataset_name} successfully added')
        logger.info(f'available objects:\n'
                    f'{get_available_objects(self.objects)}\n')

    def generate_video(self, video_path, fps, duration, objects_dict, movement_laws, self_overlay,
                       speed_interval, project_id):
        temp_objects = load_required_objects(objects_dict, self.objects)
        initialize_controllers(temp_objects, movement_laws, speed_interval,
                               self_overlay, self.backgrounds[0].shape,
                               general_transforms=self.object_general_transforms,
                               minor_transforms=self.object_minor_transforms)

        ann_keeper = AnnotationKeeper(video_shape=self.backgrounds[0].shape,
                                      current_objects=temp_objects,
                                      project_id=project_id)

        frames = generate_frames(fps, duration, self.backgrounds[0], temp_objects, ann_keeper, self.frame_transform)
        video_shape = (self.backgrounds[0].shape[1], self.backgrounds[0].shape[0])
        write_frames_to_file(video_path, fps, frames, video_shape)
        ann_keeper.upload_annotation(video_path)


if __name__ == "__main__":
    project_path = './objects/lemons_annotated'
    # project_path = './objects/small_squares'
    dataset_name = 'ds1'

    for i in range(0, 11):

        if i == 1:
            continue

        div = 0.02 * i

        general_transform = iaa.Sequential([
            iaa.Resize((1 - div * 1.2, 1 + div * 1.2)),
            iaa.Rot90((1, 4), keep_size=False),
            iaa.Rotate(rotate=(-5 - i * 5, 5 + i * 5), fit_output=True)
        ])

        minor_transform = iaa.Sequential([
            # iaa.Affine(rotate=(-5 - i, 5 + i)),
            iaa.Resize((1 - div * 1.2, 1 + div * 1.2)),
            iaa.Rotate(rotate=(-45 - i * 5, 45 + i * 5), fit_output=True),
            iaa.AddToHueAndSaturation((int(-10 - i * 1.3), int(10 + i * 1.3))),
            iaa.AddToBrightness((-2 - i * 2, 2 + i * 2)),
            iaa.AdditiveGaussianNoise(scale=(0, 10 + i * 1.5)),
            iaa.MotionBlur(k=(10, int(20 + i * 1.5)))
            # iaa.ElasticTransformation(alpha=90, sigma=9),
        ])

        frame_transform = iaa.Sometimes(0.3, iaa.Sequential([
            iaa.AddToHueAndSaturation((int(-10 - i * 1.3), int(10 + i * 1.3))),
            iaa.AddToBrightness((-2 - i * 2, 2 + i * 2)),
            iaa.AdditiveGaussianNoise(scale=(0, 10 + i * 2)),
            iaa.MotionBlur(k=(10, int(20 + i * 1.5)))
            # iaa.ElasticTransformation(alpha=90, sigma=9),
        ]))

        custom_scene = Scene(object_general_transforms=general_transform, object_minor_transforms=minor_transform,
                             frame_transform=frame_transform)
        custom_scene.add_background(f'./background_img/{i}.jpg')

        custom_scene.add_objects(project_path, dataset_name)

        fps = 5 + i * 5
        custom_scene.generate_video(video_path=f'./test{i}_{fps}fps.mp4',
                                    duration=int(900 / fps),
                                    fps=fps,
                                    objects_dict={'lemon': numpy.random.randint(2, 6)},
                                    # objects_dict={'lemon': 2, 'kiwi': 1},
                                    # objects_dict={'square': 4},
                                    movement_laws=[
                                        {'law': RandomWalkingLaw, 'params': custom_scene.backgrounds[0].shape},
                                        {'law': LinearLaw, 'params': ()}],

                                    self_overlay=0.4 + numpy.random.uniform(-0.1, 0.2),
                                    speed_interval=(5, 32 + i),
                                    project_id=4964
                                    )
