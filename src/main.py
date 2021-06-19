import random
import numpy

from init_ui import *
from init_api import *

from scene import Scene
from download_ds import download_project
from transformations import get_transforms
from functions_background import *
from movement_laws import *

project_info = app.public_api.project.get_info_by_id(PROJECT_ID)
if project_info is None:
    raise RuntimeError(f"Project id={PROJECT_ID} not found")

meta = sly.ProjectMeta.from_json(app.public_api.project.get_meta(PROJECT_ID))
if len(meta.obj_classes) == 0:
    raise ValueError("Project should have at least one class")

images_info = []

MAX_VIDEO_HEIGHT = 800  # in pixels


class SlyProgress:
    def __init__(self, api, task_id, pbar_element_name):
        self.api = api
        self.task_id = task_id

        self.pbar_element_name = pbar_element_name

        self.pbar = None

        self.refresh_params('-', 0)

    def refresh_params(self, desc, total):
        self.pbar = sly.Progress(desc, total)

    def refresh_progress(self):
        fields = [
            {"field": f"data.{self.pbar_element_name}", "payload": int(self.pbar.current * 100 / self.pbar.total)},
            {"field": f"data.{self.pbar_element_name}Message", "payload": self.pbar.message},
            {"field": f"data.{self.pbar_element_name}Current", "payload": self.pbar.current},
            {"field": f"data.{self.pbar_element_name}Total", "payload": self.pbar.total},
        ]
        self.api.task.set_fields(self.task_id, fields)

    def next_step(self):
        self.pbar.iter_done_report()
        self.refresh_progress()


def cache_images_info(api: sly.Api, PROJECT_ID):
    global images_info
    for dataset_info in api.dataset.get_list(PROJECT_ID):
        images_info.extend(api.image.get_list(dataset_info.id))


def check_setting():
    """
    @TODO:
    write function which validate required params
    """
    pass
    return 0


@app.callback("preview")
@sly.timeit
def preview(api: sly.Api, task_id, context, state, app_logger):
    sly_progress = SlyProgress(api, task_id, 'progressPreview')

    check_setting()  # check req params

    fields = [
        {"field": "data.videoUrl", "payload": None},
        {"field": "state.previewLoading", "payload": True},
    ]

    api.task.set_fields(task_id, fields)

    sly_progress.refresh_params("Downloading datasets", 2)

    download_project(project_id=PROJECT_ID,
                     dataset_ids=None,
                     all_ds=True,
                     subdir='objects')

    sly_progress.next_step()

    download_project(project_id=state['bgProjectId'],
                     dataset_ids=state['bgDatasets'],
                     all_ds=state['allDatasets'],
                     subdir='backgrounds')

    sly_progress.next_step()

    project_path = os.path.join(app.data_dir, 'objects')  # init scene
    dataset_names = [name for name in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, name))]

    _, minor_transform, frame_transform = get_transforms(5)

    background_paths = get_background_paths(app.data_dir)

    custom_scene = Scene(object_general_transforms=None, object_minor_transforms=minor_transform,
                         frame_transform=frame_transform)

    custom_scene.add_background(background_paths[random.randint(0, len(background_paths) - 1)])
    custom_scene.add_objects(project_path, dataset_names)

    fps = state['fps']

    video_path = os.path.join(app.data_dir, './preview.mp4')

    movement_laws = load_movements_laws(custom_scene=custom_scene,
                                        req_laws={'linearLaw': state['linearLaw'],
                                                  'randomLaw': state['randomLaw']})

    custom_scene.generate_video(video_path=video_path,  # generate video
                                duration=5,
                                fps=fps,
                                objects_dict={'lemon': numpy.random.randint(1, 2)},
                                movement_laws=movement_laws,
                                self_overlay=0.4 + numpy.random.uniform(-0.1, 0.2),
                                speed_interval=tuple(state['speedInterval']),
                                project_id=None,
                                project_name='SLYvSynth',
                                upload_ann=False,
                                sly_progress=sly_progress
                                )

    remote_video_path = os.path.join(f"/SLYvSynth/{task_id}", "preview.mp4")
    if api.file.exists(TEAM_ID, remote_video_path):
        api.file.remove(TEAM_ID, remote_video_path)
    file_info = api.file.upload(TEAM_ID, video_path, remote_video_path)

    print(file_info.full_storage_url)
    fields = [
        {"field": "data.videoUrl", "payload": file_info.full_storage_url},
        {"field": "state.previewLoading", "payload": False},
    ]
    api.task.set_fields(task_id, fields)


@app.callback("synthesize")
@sly.timeit
def synthesize(api: sly.Api, task_id, context, state, app_logger):
    sly_progress = SlyProgress(api, task_id, 'progressSynth')

    check_setting()  # check req params

    sly_progress.refresh_params("Downloading datasets", 2)

    download_project(project_id=PROJECT_ID,
                     dataset_ids=None,
                     all_ds=True,
                     subdir='objects')

    sly_progress.next_step()

    download_project(project_id=state['bgProjectId'],
                     dataset_ids=state['bgDatasets'],
                     all_ds=state['allDatasets'],
                     subdir='backgrounds')

    sly_progress.next_step()

    project_path = os.path.join(app.data_dir, 'objects')  # init scene
    dataset_names = [name for name in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, name))]

    _, minor_transform, frame_transform = get_transforms(5)

    background_paths = get_background_paths(app.data_dir)

    custom_scene = Scene(object_general_transforms=None, object_minor_transforms=minor_transform,
                         frame_transform=frame_transform)

    custom_scene.add_background(background_paths[random.randint(0, len(background_paths) - 1)])
    custom_scene.add_objects(project_path, dataset_names)

    fps = state['fps']
    duration = 5

    video_path = os.path.join(app.data_dir, f'./{duration}sec_{fps}fps.mp4')

    movement_laws = load_movements_laws(custom_scene=custom_scene,
                                        req_laws={'linearLaw': state['linearLaw'],
                                                  'randomLaw': state['randomLaw']})

    custom_scene.generate_video(video_path=video_path,  # generate video
                                duration=5,
                                fps=fps,
                                objects_dict={'lemon': numpy.random.randint(1, 2)},
                                movement_laws=movement_laws,
                                self_overlay=0.4 + numpy.random.uniform(-0.1, 0.2),
                                speed_interval=tuple(state['speedInterval']),
                                project_id=None,
                                project_name=state["resProjectName"],
                                upload_ann=True,
                                sly_progress=sly_progress
                                )

    res_project = api.project.get_info_by_id(custom_scene.ann_keeper.project.id)
    fields = [
        {"field": "data.started", "payload": False},
        {"field": "data.resProjectId", "payload": res_project.id},
        {"field": "data.resProjectName", "payload": res_project.name},
        {"field": "data.resProjectPreviewUrl",
         "payload": api.image.preview_url(res_project.reference_image_url, 100, 100)},
    ]
    api.task.set_fields(task_id, fields)
    api.task.set_output_project(task_id, res_project.id, res_project.name)
    app.stop()


def main():
    data = {}
    state = {}

    init_input_project(app.public_api, data, project_info)
    init_settings(state)
    init_res_project(data, state, project_info)

    data["videoUrl"] = None

    data["progressSynth"] = 0
    data["progressSynthMessage"] = "-"
    data["progressSynthCurrent"] = 0
    data["progressSynthTotal"] = 0

    state["previewLoading"] = False
    data["progressPreview"] = 0
    data["progressPreviewMessage"] = "-"
    data["progressPreviewCurrent"] = 0
    data["progressPreviewTotal"] = 0

    cache_images_info(app.public_api, PROJECT_ID)
    app.run(data=data, state=state)


if __name__ == "__main__":
    sly.main_wrapper("main", main)
