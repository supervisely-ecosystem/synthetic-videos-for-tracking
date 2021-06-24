import random
import numpy
import sys

from sly_globals import *

from init_ui import *

from scene import *
from pathlib import Path
from download_data import *
from transformations import get_transforms
from functions_background import *
from movement_laws import *


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

    video_path = os.path.join(app.data_dir, './preview.mp4')
    remote_video_path = os.path.join(f"/SLYvSynth/{task_id}", "preview.mp4")
    if api.file.exists(team_id, remote_video_path):
        api.file.remove(team_id, remote_video_path)
    file_info = api.file.upload(team_id, video_path, remote_video_path)

    fields = [
        {"field": "data.videoUrl", "payload": file_info.full_storage_url},
        {"field": "state.previewLoading", "payload": False},
    ]
    api.task.set_fields(task_id, fields)


@app.callback("synthesize")
@sly.timeit
def synthesize(api: sly.Api, task_id, context, state, app_logger):
    sly_progress = SlyProgress(api, task_id, 'progressSynth')

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


def main():
    data = {}
    state = {}

    init_ui(data, state)

    app.compile_template(root_source_dir)
    app.run(data=data, state=state)


if __name__ == "__main__":
    sly.main_wrapper("main", main)
