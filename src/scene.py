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

        self.ann_keeper = None

    def add_backgrounds(self, background_paths):
        for background_path in background_paths:
            self.backgrounds.append(get_cv2_background_by_path(background_path))
        logger.info(f'{len(self.backgrounds)} backgrounds successfully added')

    def add_objects(self, req_objects):

        self.objects = get_objects_list_for_project(req_objects)

        logger.info(f'[{len(self.objects)}] objects successfully added')
        logger.info(f'available objects:\n'
                    f'{get_available_objects(self.objects)}\n')

    def generate_video(self, video_path, fps, duration, movement_laws, self_overlay,
                       speed_interval,
                       project_id=None, project_name='SLYvSynth',
                       upload_ann=False, sly_progress=None):

        temp_objects = self.objects
        initialize_controllers(temp_objects, movement_laws, speed_interval,
                               self_overlay, self.backgrounds[0].shape,
                               general_transforms=self.object_general_transforms,
                               minor_transforms=self.object_minor_transforms)

        ann_keeper = AnnotationKeeper(video_shape=self.backgrounds[0].shape,
                                      current_objects=temp_objects)

        frames = generate_frames(fps, duration, self.backgrounds[0], temp_objects, ann_keeper, self.frame_transform,
                                 sly_progress)

        video_shape = (self.backgrounds[0].shape[1], self.backgrounds[0].shape[0])
        write_frames_to_file(video_path, fps, frames, video_shape, sly_progress)

        if upload_ann:
            ann_keeper.init_project_remotely(project_id=project_id, project_name=project_name)
            ann_keeper.upload_annotation(video_path)

        self.ann_keeper = ann_keeper


if __name__ == "__main__":
    project_path = './objects/lemons_annotated'
    # project_path = './objects/small_squares'
    dataset_names = ['ds1']

    for i in range(3, 11):

        div = 0.02 * i

        general_transform = iaa.Sequential([
            iaa.Sometimes(0.3, iaa.Resize((1 - div * 2, 1 + div * 2), interpolation='cubic')),
            # iaa.Rot90((1, 4), keep_size=False),
            # iaa.Rotate(rotate=(-5 - i * 5, 5 + i * 5), fit_output=True)
        ])

        minor_transform = iaa.Sequential([
            # iaa.Affine(rotate=(-5 - i, 5 + i)),
            iaa.Resize((1 - div * 1.2, 1 + div * 1.2)),
            # iaa.Rotate(rotate=(-45 - i * 5, 45 + i * 5), fit_output=True),
            iaa.Rotate(rotate=(1, 360), fit_output=True),
            # iaa.Fliplr(p=0.5),
            iaa.AddToHueAndSaturation((int(-10 - i * 1.3), int(10 + i * 1.3))),
            iaa.AddToBrightness((-2 - i * 2, 2 + i * 2)),
            iaa.AdditiveGaussianNoise(scale=(0, 10 + i * 1.5)),
            iaa.MotionBlur(k=(10, int(20 + i * 1.5))),
            iaa.Sometimes(0.3, iaa.ElasticTransformation(alpha=90, sigma=9)),
        ])

        frame_transform = iaa.Sometimes(0.3, iaa.Sequential([
            iaa.AddToHueAndSaturation((int(-10 - i * 1.3), int(10 + i * 1.3))),
            iaa.AddToBrightness((-2 - i * 2, 2 + i * 2)),
            # iaa.Rotate(rotate=(-4, 4), fit_output=True),
            iaa.AdditiveGaussianNoise(scale=(0, 10 + i * 2)),
            iaa.MotionBlur(k=(10, int(20 + i * 1.5)))
            # iaa.ElasticTransformation(alpha=90, sigma=9),
        ]))

        custom_scene = Scene(object_general_transforms=None, object_minor_transforms=minor_transform,
                             frame_transform=frame_transform)
        custom_scene.add_backgrounds(f'./background_img/{i}.jpg')

        custom_scene.add_objects(project_path, dataset_names)

        fps = 15
        custom_scene.generate_video(video_path=f'./test{i}_{fps}fps.mp4',
                                    duration=int(900 / fps),
                                    # duration=10,
                                    fps=fps,
                                    objects_dict={'lemon': 6},
                                    # objects_dict={'lemon': 2, 'kiwi': 1},
                                    # objects_dict={'square': 4},
                                    movement_laws=[
                                        {'law': RandomWalkingLaw, 'params': custom_scene.backgrounds[0].shape},
                                        {'law': LinearLaw, 'params': ()}],

                                    self_overlay=0.1 + numpy.random.uniform(-0.1, 0.3),
                                    speed_interval=(1, 15 + i),
                                    project_id=5029,
                                    project_name="TEST6_SINGLECLASS",
                                    upload_ann=True,
                                    )
