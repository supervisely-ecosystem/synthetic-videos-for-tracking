import math
import numpy
import random
import supervisely_lib as sly
import imgaug.augmenters as iaa
from supervisely_lib.geometry.sliding_windows_fuzzy import SlidingWindowsFuzzy, SlidingWindowBorderStrategy

import init_ui
from scene import Scene
from functions_objects import *
from functions_video import *
from movement_laws import *
from init_api import *


app: sly.AppService = sly.AppService()

project_info = app.public_api.project.get_info_by_id(PROJECT_ID)
if project_info is None:
    raise RuntimeError(f"Project id={PROJECT_ID} not found")

meta = sly.ProjectMeta.from_json(app.public_api.project.get_meta(PROJECT_ID))
if len(meta.obj_classes) == 0:
    raise ValueError("Project should have at least one class")

images_info = []

MAX_VIDEO_HEIGHT = 800  # in pixels


def cache_images_info(api: sly.Api, PROJECT_ID):
    global images_info
    for dataset_info in api.dataset.get_list(PROJECT_ID):
        images_info.extend(api.image.get_list(dataset_info.id))


def refresh_progress_preview(api: sly.Api, task_id, progress: sly.Progress):
    fields = [
        {"field": "data.progressPreview", "payload": int(progress.current * 100 / progress.total)},
        {"field": "data.progressPreviewMessage", "payload": progress.message},
        {"field": "data.progressPreviewCurrent", "payload": progress.current},
        {"field": "data.progressPreviewTotal", "payload": progress.total},
    ]
    api.task.set_fields(task_id, fields)


@app.callback("preview")
@sly.timeit
def preview(api: sly.Api, task_id, context, state, app_logger):
    fields = [
        {"field": "data.videoUrl", "payload": None},
        {"field": "state.previewLoading", "payload": True},
    ]
    api.task.set_fields(task_id, fields)

    slider = SlidingWindowsFuzzy([state["windowHeight"], state["windowWidth"]],
                                 [state["overlapY"], state["overlapX"]],
                                 state["borderStrategy"])
    image_info = random.choice(images_info)
    img = api.image.download_np(image_info.id)

    ann_json = api.annotation.download(image_info.id).annotation
    ann = sly.Annotation.from_json(ann_json, meta)

    if state["drawLabels"] is True:
        ann.draw_pretty(img, thickness=3)

    h, w = img.shape[:2]
    max_right = w - 1
    max_bottom = h - 1
    rectangles = []
    for window in slider.get(img.shape[:2]):
        rectangles.append(window)
        max_right = max(max_right, window.right)
        max_bottom = max(max_bottom, window.bottom)

    if max_right > w or max_bottom > h:
        sly.logger.debug("Padding", extra={"h": h, "w": w, "max_right": max_right, "max_bottom": max_bottom})
        aug = iaa.PadToFixedSize(width=max_right, height=max_bottom, position='right-bottom')
        img = aug(image=img)
        #sly.image.write(os.path.join(app.data_dir, "padded.jpg"), img)

    frame_img = img.copy()
    resize_aug = None
    if frame_img.shape[0] > MAX_VIDEO_HEIGHT:
        resize_aug = iaa.Resize({"height": MAX_VIDEO_HEIGHT, "width": "keep-aspect-ratio"})
        frame_img = resize_aug(image=frame_img.copy())
    height, width, channels = frame_img.shape

    video_path = os.path.join(app.data_dir, "preview.mp4")
    sly.fs.ensure_base_path(video_path)
    sly.fs.silent_remove(video_path)
    video = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'VP90'), state["fps"], (width, height))
    report_every = max(5, math.ceil(len(rectangles) / 100))
    progress = sly.Progress("Rendering frames", len(rectangles))
    refresh_progress_preview(api, task_id, progress)
    for i, rect in enumerate(rectangles):
        frame = img.copy()
        rect: sly.Rectangle
        rect.draw_contour(frame, [255, 0, 0], thickness=5)
        if resize_aug is not None:
            frame = resize_aug(image=frame)
        #sly.image.write(os.path.join(app.data_dir, f"{i:05d}.jpg"), frame)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        video.write(frame_bgr)

        progress.iter_done_report()
        if i % report_every == 0:
            refresh_progress_preview(api, task_id, progress)

    progress = sly.Progress("Saving video file", 1)
    progress.iter_done_report()
    refresh_progress_preview(api, task_id, progress)
    video.release()

    progress = sly.Progress("Uploading video", 1)
    progress.iter_done_report()
    refresh_progress_preview(api, task_id, progress)
    remote_video_path = os.path.join(f"/SLYvSynth/{task_id}", "preview.mp4")
    if api.file.exists(TEAM_ID, remote_video_path):
        api.file.remove(TEAM_ID, remote_video_path)
    file_info = api.file.upload(TEAM_ID, video_path, remote_video_path)

    fields = [
        {"field": "state.previewLoading", "payload": False},
        {"field": "data.videoUrl", "payload": file_info.full_storage_url},
    ]
    api.task.set_fields(task_id, fields)

#
# def refresh_progress_split(api: sly.Api, task_id, progress: sly.Progress):
#     fields = [
#         {"field": "data.progress", "payload": int(progress.current * 100 / progress.total)},
#         {"field": "data.progressCurrent", "payload": progress.current},
#         {"field": "data.progressTotal", "payload": progress.total},
#     ]
#     api.task.set_fields(task_id, fields)
#
#
# @app.callback("gen_video")
# @sly.timeit
# def split(api: sly.Api, task_id, context, state, app_logger):
#     for i in range(0, 11):
#         if i == 1:
#             continue
#
#         div = 0.02 * i
#         general_transform = iaa.Sequential([
#             iaa.Resize((1 - div * 1.2, 1 + div * 1.2)),
#             iaa.Rot90((1, 4), keep_size=False),
#             iaa.Rotate(rotate=(-5 - i * 5, 5 + i * 5), fit_output=True)
#         ])
#
#         minor_transform = iaa.Sequential([
#             # iaa.Affine(rotate=(-5 - i, 5 + i)),
#             iaa.Resize((1 - div * 1.2, 1 + div * 1.2)),
#             iaa.Rotate(rotate=(-45 - i * 5, 45 + i * 5), fit_output=True),
#             iaa.AddToHueAndSaturation((int(-10 - i * 1.3), int(10 + i * 1.3))),
#             iaa.AddToBrightness((-2 - i * 2, 2 + i * 2)),
#             iaa.AdditiveGaussianNoise(scale=(0, 10 + i * 1.5)),
#             iaa.MotionBlur(k=(10, int(20 + i * 1.5)))
#             # iaa.ElasticTransformation(alpha=90, sigma=9),
#         ])
#
#         frame_transform = iaa.Sometimes(0.3, iaa.Sequential([
#             iaa.AddToHueAndSaturation((int(-10 - i * 1.3), int(10 + i * 1.3))),
#             iaa.AddToBrightness((-2 - i * 2, 2 + i * 2)),
#             iaa.AdditiveGaussianNoise(scale=(0, 10 + i * 2)),
#             iaa.MotionBlur(k=(10, int(20 + i * 1.5)))
#             # iaa.ElasticTransformation(alpha=90, sigma=9),
#         ]))
#
#         custom_scene = Scene(object_general_transforms=general_transform, object_minor_transforms=minor_transform,
#                              frame_transform=frame_transform)
#         custom_scene.add_background(f'./background_img/{i}.jpg')
#
#         custom_scene.add_objects(project_path, dataset_name)
#
#         fps = 5 + i * 5
#         custom_scene.generate_video(video_path=f'./test{i}_{fps}fps.mp4',
#                                     duration=int(900 / fps),
#                                     fps=fps,
#                                     objects_dict={'lemon': numpy.random.randint(2, 6)},
#                                     # objects_dict={'lemon': 2, 'kiwi': 1},
#                                     # objects_dict={'square': 4},
#                                     movement_laws=[
#                                         {'law': RandomWalkingLaw, 'params': custom_scene.backgrounds[0].shape},
#                                         {'law': LinearLaw, 'params': ()}],
#
#                                     self_overlay=0.4 + numpy.random.uniform(-0.1, 0.2),
#                                     speed_interval=(5, 32 + i),
#                                     PROJECT_ID=4964
#                                     )
#     app.stop()


def main():
    data = {}
    state = {}

    init_ui.init_input_project(app.public_api, data, project_info)
    init_ui.init_settings(state)
    init_ui.init_res_project(data, state, project_info)

    data["videoUrl"] = None

    data["progress"] = 0
    data["progressCurrent"] = 0
    data["progressTotal"] = 0

    state["previewLoading"] = False
    data["progressPreview"] = 0
    data["progressPreviewMessage"] = "Rendering frames"
    data["progressPreviewCurrent"] = 0
    data["progressPreviewTotal"] = 0

    cache_images_info(app.public_api, PROJECT_ID)
    app.run(data=data, state=state)


if __name__ == "__main__":
    sly.main_wrapper("main", main)
