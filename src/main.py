from sly_globals import *

from functools import partial

from init_ui import init_ui
from download_data import SlyProgress
from functions_video import process_video


@app.callback("preview")
@sly.timeit
def preview(api: sly.Api, task_id, context, state, app_logger):
    sly_progress = SlyProgress(api, task_id, 'progressPreview')

    fields = [
        {"field": "data.videoUrl", "payload": None},
        {"field": "state.previewLoading", "payload": True},
    ]

    api.task.set_fields(task_id, fields)

    rc, _ = process_video(sly_progress, state, is_preview=True)

    if rc == 0:
        sly_progress.refresh_params('Uploading video', 0, True)
        progress_cb = partial(sly_progress.upload_monitor, api=api, task_id=task_id, progress=sly_progress.pbar)

        video_path = os.path.join(app.data_dir, './preview.mp4')
        remote_video_path = os.path.join(f"/SLYvSynth/{task_id}", "preview.mp4")
        if api.file.exists(team_id, remote_video_path):
            api.file.remove(team_id, remote_video_path)

        file_info = api.file.upload(team_id, video_path, remote_video_path, progress_cb=progress_cb)

        sly_progress.next_step()
        sly_progress.reset_params()

        fields = [
            {"field": "data.videoUrl", "payload": file_info.full_storage_url},
            {"field": "state.previewLoading", "payload": False},
        ]
        api.task.set_fields(task_id, fields)
    else:  # @TODO: process errors
        fields = [
            {"field": "data.videoUrl", "payload": None},
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

    rc, res_project_id = process_video(sly_progress, state, is_preview=False)

    sly_progress.reset_params()
    if rc == 0:
        res_project = api.project.get_info_by_id(res_project_id)  # load full project info

        fields = [
            {"field": "state.step6Loading", "payload": False},
            {"field": "state.done6", "payload": True},

            {"field": "data.dstProjectId", "payload": res_project.id},
            {"field": "data.dstProjectName", "payload": res_project.name},
            {"field": "data.dstProjectPreviewUrl",
             "payload": api.image.preview_url(res_project.reference_image_url, 100, 100)},
        ]
        api.task.set_fields(task_id, fields)
        api.task.set_output_project(task_id, res_project.id, res_project.name)

    else:
        fields = [
            {"field": "state.step6Loading", "payload": False},
        ]
        api.task.set_fields(task_id, fields)


    # app.stop()


@app.callback("restart")
@sly.timeit
def restart(api: sly.Api, task_id, context, state, app_logger):
    data = {}

    init_ui(data, state)
    restart_from_step = state['restartFrom']

    fields = [
        {"field": "data", "payload": data, "append": True, "recursive": False},
        {"field": "state", "payload": state, "append": True, "recursive": False},
        {"field": "state.restartFrom", "payload": None},
        {"field": "state.activeStep", "payload": restart_from_step},
        {"field": f"state.disabled{restart_from_step}", "payload": False},
        {"field": f"state.collapsed{restart_from_step}", "payload": False},
    ]

    api.app.set_fields(task_id, fields)
    api.app.set_field(task_id, "data.scrollIntoView", f"step{restart_from_step}")


def main():
    data = {}
    state = {'restartFrom': None}

    init_ui(data, state)

    app.compile_template(root_source_dir)
    app.run(data=data, state=state)


if __name__ == "__main__":
    sly.main_wrapper("main", main)
