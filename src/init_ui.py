import os
import supervisely_lib as sly

from augmentations import init_augs

from sly_globals import *

import math


class SlyProgress:
    def __init__(self, api, task_id, pbar_element_name):
        self.api = api
        self.task_id = task_id
        self.pbar_element_name = pbar_element_name
        self.pbar = None

    def refresh_params(self, desc, total, is_size=False):
        self.pbar = sly.Progress(desc, total, is_size=is_size)
        if self.pbar.total != 0:
            self.refresh_progress()

    def refresh_progress(self):
        fields = [
            {"field": f"data.{self.pbar_element_name}", "payload": math.floor(self.pbar.current * 100 /
                                                                              self.pbar.total)},
            {"field": f"data.{self.pbar_element_name}Message", "payload": self.pbar.message},
            {"field": f"data.{self.pbar_element_name}Current", "payload": self.pbar.current},
            {"field": f"data.{self.pbar_element_name}Total", "payload": self.pbar.total},
        ]
        self.api.task.set_fields(self.task_id, fields)

    def next_step(self):
        self.pbar.iter_done_report()
        self.refresh_progress()

    def upload_monitor(self, monitor, api: sly.Api, task_id, progress: sly.Progress):
        if progress.total == 0:
            progress.set(monitor.bytes_read, monitor.len, report=False)
        else:
            progress.set_current_value(monitor.bytes_read, report=False)
        self.refresh_progress()

    def update_progress(self, count, api: sly.Api, task_id, progress: sly.Progress):
        # hack slight inaccuracies in size convertion
        count = min(count, progress.total - progress.current)
        progress.iters_done(count)
        if progress.need_report():
            progress.report_progress()
            self.refresh_progress()

    def set_progress(self, current, api: sly.Api, task_id, progress: sly.Progress):

        old_value = progress.current
        delta = current - old_value
        self.update_progress(delta, api, task_id, progress)


def init_input_project(data, state):
    data["projectId"] = project_info.id
    data["projectName"] = project_info.name
    data["projectPreviewUrl"] = api.image.preview_url(project_info.reference_image_url, 100, 100)
    data["projectItemsCount"] = project_info.items_count

    state["bgTeamId"] = None
    state["bgWorkspaceId"] = None
    state["bgProjectId"] = None
    state["bgDatasets"] = []
    state["allDatasets"] = True

    state["showCanResizeWindow"] = False
    state["canResize"] = False




def init_step_flags(data, state):

    if state['restartFrom']:
        start_step = state['restartFrom']
    else:
        start_step = 1

    for step in range(start_step, 6):
        state[f'done{step}'] = False
        state[f"step{step}Loading"] = False
        state[f"disabled{step}"] = True
        state[f'collapsed{step}'] = True

    state[f'collapsed1'] = False
    state[f'disabled1'] = False


def init_settings(data, state):
    state["activeStep"] = 1

    data["videoUrl"] = None
    state["previewLoading"] = False

    state["speedInterval"] = [5, 20]
    state["objectOverlayInterval"] = [0.4, 0.6]
    state["linearLaw"] = True
    state["randomLaw"] = True
    state["fps"] = 25
    # state["fps"] = 10

    state["durationPreview"] = 1
    state["durationVideo"] = 60
    # state["durationVideo"] = 1


def init_output_project(data, state):
    state["dstProjectMode"] = "newProject"
    state["dstProjectName"] = "my_videos"
    state["dstProjectId"] = None

    state["dstDatasetMode"] = "newDataset"
    state["dstDatasetName"] = "my_dataset"
    state["selectedDatasetName"] = None

    data["workspaceId"] = workspace_id

    data["dstProjectPreviewUrl"] = None


def generate_rows_by_ann(ann_meta):
    rows = []

    for curr_class in ann_meta['classes']:
        rows.append({
            "Name": f"{curr_class['title']}",
            "Shape": f"{curr_class['shape']}",
            "Color": f"{curr_class['color']}",
        })

    return rows


def init_objects_table(data, state):
    columns = [
        {"title": "Name", "subtitle": "label in project"},
        {"title": "Shape", "subtitle": "shape type"},
        {"title": "Color", "subtitle": "color of mask"},
        {"title": "Count", "subtitle": "count to add"},
        {"title": "Positive", "subtitle": "track that object"},
    ]

    data["myColumns"] = columns

    objects_project_meta = api.project.get_meta(id=project_id)

    rows = generate_rows_by_ann(objects_project_meta)

    data["myRows"] = rows

    state["classCounts"] = {
        row['Name']: 0 for row in rows
    }
    state["classIsPositive"] = {
        row['Name']: True for row in rows
    }


def init_progress_bars(data, state):
    progress_names = ['DownloadBackgrounds', 'DownloadObjects', 'Preview', 'Synth', '4']

    for progress_name in progress_names:
        data[f"progress{progress_name}"] = 0
        data[f"progress{progress_name}Message"] = "-"
        data[f"progress{progress_name}Current"] = 0
        data[f"progress{progress_name}Total"] = 0


def init_interface_by_step(data, state):
    if state['restartFrom']:
        start_step = state['restartFrom']
    else:
        start_step = 1

    for curr_step in range(start_step, 6):
        if curr_step == 1:
            init_input_project(data, state)  # step 1
            init_objects_table(data, state)
        if curr_step == 2:
            init_augs(data, state)  # step 2
        if curr_step == 3:
            init_settings(data, state)  # step 3
        if curr_step == 4:
            init_output_project(data, state)  # step 4


def init_ui(data, state):


    init_step_flags(data, state)

    init_progress_bars(data, state)

    init_interface_by_step(data, state)

