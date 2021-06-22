import random
import numpy

from init_ui import *
from init_api import *

from scene import Scene
from download_ds import *
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


class SlyProgress:
    def __init__(self, api, task_id, pbar_element_name):
        self.api = api
        self.task_id = task_id
        self.pbar_element_name = pbar_element_name
        self.pbar = None
        # self.refresh_params('-', 0)

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


def process_video(sly_progress, state, is_preview=True):
    sly_progress.refresh_params("Downloading datasets", 2)

    objects_ann_info = get_project_ann_info(project_id=PROJECT_ID,
                                            dataset_names=None,
                                            all_ds=True)

    sly_progress.next_step()

    backgrounds_ann_info = get_project_ann_info(project_id=state['bgProjectId'],
                                                dataset_names=state['bgDatasets'],
                                                all_ds=state['allDatasets'])

    sly_progress.next_step()

    req_objects = get_list_req_objects(objects_ann_info, state)  # init scene
    req_backgrounds = get_list_req_backgrounds(backgrounds_ann_info, state)

    download_images(req_objects, 'objects')
    download_images(req_backgrounds, 'backgrounds')

    _, minor_transform, frame_transform = get_transforms(5)

    background_paths = [curr_background.image_path for curr_background in req_backgrounds]

    custom_scene = Scene(object_general_transforms=None, object_minor_transforms=minor_transform,
                         frame_transform=frame_transform)

    if is_preview:
        custom_scene.add_backgrounds([background_paths[random.randint(0, len(background_paths) - 1)]])
    else:
        custom_scene.add_backgrounds(background_paths)

    custom_scene.add_objects(req_objects)

    fps = state['fps']

    if is_preview:
        duration = state['durationPreview']
    else:
        duration = state['durationVideo']

    if is_preview:
        video_path = os.path.join(app.data_dir, './preview.mp4')
    else:
        video_path = os.path.join(app.data_dir, f'./{duration}sec_{fps}fps.mp4')

    movement_laws = load_movements_laws(custom_scene=custom_scene,
                                        req_laws={'linearLaw': state['linearLaw'],
                                                  'randomLaw': state['randomLaw']})

    custom_scene.generate_video(video_path=video_path,  # generate video
                                duration=duration,
                                fps=fps,
                                movement_laws=movement_laws,
                                self_overlay=tuple(state['objectOverlayInterval']),
                                speed_interval=tuple(state['speedInterval']),
                                project_id=None,
                                project_name=state["resProjectName"],
                                upload_ann=False if is_preview else True,
                                sly_progress=sly_progress
                                )

    if custom_scene.ann_keeper.project:
        return custom_scene.ann_keeper.project.id


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

    process_video(sly_progress, state, is_preview=True)

    video_path = os.path.join(app.data_dir, './preview.mp4')
    remote_video_path = os.path.join(f"/SLYvSynth/{task_id}", "preview.mp4")
    if api.file.exists(TEAM_ID, remote_video_path):
        api.file.remove(TEAM_ID, remote_video_path)
    file_info = api.file.upload(TEAM_ID, video_path, remote_video_path)

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

    res_project = process_video(sly_progress, state, is_preview=False)

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


def init_objects_table(data, state):
    columns = [
        {"title": "Name", "subtitle": "label in project"},
        {"title": "Shape", "subtitle": "shape type"},
        {"title": "Color", "subtitle": "color of mask"},
        {"title": "Count", "subtitle": "count to add"},
        {"title": "Positive", "subtitle": "track that object"},
    ]

    data["myColumns"] = columns

    objects_project_meta = api.project.get_meta(id=PROJECT_ID)

    rows = generate_rows_by_ann(objects_project_meta)

    data["myRows"] = rows

    state["classCounts"] = {
        row['Name']: 0 for row in rows
    }
    state["classIsPositive"] = {
        row['Name']: True for row in rows
    }


def init_progress_bars(data, state):
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


def main():
    data = {}
    state = {}

    init_input_project(app.public_api, data, project_info)
    init_settings(state)
    init_res_project(data, state, project_info)

    init_progress_bars(data, state)
    init_objects_table(data, state)

    cache_images_info(app.public_api, PROJECT_ID)
    app.run(data=data, state=state)


if __name__ == "__main__":
    sly.main_wrapper("main", main)
