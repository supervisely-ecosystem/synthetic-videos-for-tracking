import random
import numpy
import sys

from sly_globals import *
from init_ui import *
from scene import *
from download_data import *

from functions_background import *



@app.callback("preview")
@sly.timeit
def preview(api: sly.Api, task_id, context, state, app_logger):
    sly_progress = SlyProgress(api, task_id, 'progressPreview')

    fields = [
        {"field": "data.videoUrl", "payload": None},
        {"field": "state.previewLoading", "payload": True},
    ]

    api.task.set_fields(task_id, fields)

    process_video(sly_progress, state, is_preview=True)
    sly_progress.refresh_params('Uploading video', 1)

    video_path = os.path.join(app.data_dir, './preview.mp4')
    remote_video_path = os.path.join(f"/SLYvSynth/{task_id}", "preview.mp4")
    if api.file.exists(team_id, remote_video_path):
        api.file.remove(team_id, remote_video_path)

    # file_info = api.file.upload(team_id, video_path, remote_video_path, progress_cb=sly_progress.pbar.iters_done_report)
    file_info = api.file.upload(team_id, video_path, remote_video_path)

    sly_progress.next_step()

    fields = [
        {"field": "data.videoUrl", "payload": file_info.full_storage_url},
        {"field": "state.previewLoading", "payload": False},
    ]
    api.task.set_fields(task_id, fields)


def reset_output_headers_by_state(state):
    if state["dstProjectMode"] == "newProject":
        state["dstProjectId"] = None

    if state["dstDatasetMode"] == "newDataset":
        state["selectedDatasetName"] = None


@app.callback("synthesize")
@sly.timeit
def synthesize(api: sly.Api, task_id, context, state, app_logger):
    sly_progress = SlyProgress(api, task_id, 'progressSynth')

    reset_output_headers_by_state(state)

    res_project_id = process_video(sly_progress, state, is_preview=False)

    res_project = api.project.get_info_by_id(res_project_id)  # load full project info

    fields = [
        {"field": "data.step5Loading", "payload": False},
        {"field": "data.done5", "payload": True},


        {"field": "data.dstProjectId", "payload": res_project.id},
        {"field": "data.dstProjectName", "payload": res_project.name},
        {"field": "data.dstProjectPreviewUrl",
         "payload": api.image.preview_url(res_project.reference_image_url, 100, 100)},
    ]
    api.task.set_fields(task_id, fields)
    api.task.set_output_project(task_id, res_project.id, res_project.name)
    # app.stop()


def main():
    data = {}
    state = {}

    init_ui(data, state)

    app.compile_template(root_source_dir)
    app.run(data=data, state=state)


if __name__ == "__main__":
    sly.main_wrapper("main", main)
