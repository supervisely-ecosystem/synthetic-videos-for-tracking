import os
import supervisely_lib as sly

from ui.augs import init_augs

from sly_globals import *
from download_data import generate_rows_by_ann


def init_input_project(data, state):
    data["projectId"] = project_info.id
    data["projectName"] = project_info.name
    data["projectPreviewUrl"] = api.image.preview_url(project_info.reference_image_url, 100, 100)
    data["projectItemsCount"] = project_info.items_count


def init_step_flags(data, state):
    for step in range(1, 3):
        data[f'done{step}'] = False
        state[f"disabled{step}"] = False  # while debuggin
        data[f"step{step}Loading"] = False


def init_settings(data, state):
    state["activeStep"] = 1
    state["activeStepAug"] = 1

    state["bgTeamId"] = None
    state["bgWorkspaceId"] = None
    state["bgProjectId"] = None
    state["bgDatasets"] = []
    state["allDatasets"] = True

    state["speedInterval"] = [5, 20]
    state["objectOverlayInterval"] = [0.4, 0.6]
    state["linearLaw"] = True
    state["randomLaw"] = True
    state["fps"] = 25

    state["durationPreview"] = 1
    state["durationVideo"] = 60


def init_res_project(data, state):
    data["videoUrl"] = None

    data["resProjectId"] = None
    state["resProjectName"] = f"synthesized_{project_info.name}_{state['fps']}fps"
    data["resProjectName"] = None
    data["resProjectPreviewUrl"] = None
    data["started"] = False


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
    progress_names = ['1', 'Preview', 'Synth']

    for progress_name in progress_names:
        data[f"progress{progress_name}"] = 0
        data[f"progress{progress_name}Message"] = "-"
        data[f"progress{progress_name}Current"] = 0
        data[f"progress{progress_name}Total"] = 0


def init_ui(data, state):
    init_step_flags(data, state)

    init_settings(data, state)

    init_progress_bars(data, state)

    init_input_project(data, state)  # step 1
    init_objects_table(data, state)

    init_augs(data, state)  # step 2

    init_res_project(data, state)  # step N

