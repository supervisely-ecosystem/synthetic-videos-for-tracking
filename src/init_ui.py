from sly_globals import *
import math
from augmentations import init_augs


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
    state["canResize"] = True  # hardcoded
    state["loadStats"] = False
    state["step2StatsLoading"] = False





def init_step_flags(data, state):

    if state['restartFrom']:
        start_step = state['restartFrom']
    else:
        start_step = 1

    for step in range(start_step, 7):
        state[f'done{step}'] = False
        state[f"step{step}Loading"] = False
        state[f"disabled{step}"] =  True
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
    state['videoSynthNum'] = 1

    state["dstProjectMode"] = "newProject"
    state["dstProjectName"] = "my_videos"
    state["dstProjectId"] = None

    state["dstDatasetMode"] = "newDataset"
    state["dstDatasetName"] = "my_dataset"
    state["selectedDatasetName"] = None

    data["workspaceId"] = workspace_id

    data["dstProjectPreviewUrl"] = None


def split_rows(rows):
    pos_rows = []
    neg_rows = []

    for row in rows:
        if row['Shape'] == 'bitmap':
            pos_rows.append(row)
        else:
            neg_rows.append(row)

    return pos_rows, neg_rows


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

    pos_columns = [
        {"title": "Name", "subtitle": "label in project"},
        {"title": "Labeled images", "subtitle": "labeled images"},
        {"title": "Labeled objects", "subtitle": "count of labeled"},
        {"title": "Shape", "subtitle": "shape type"},
        {"title": "Color", "subtitle": "color of mask"},
        {"title": "Objects count", "subtitle": "how many objects this class will be on each frame"},
        {"title": "Positive", "subtitle": "track that object"},
    ]

    neg_columns = [
        {"title": "Name", "subtitle": "label in project"},
        {"title": "Labeled images", "subtitle": "labeled images"},
        {"title": "Labeled objects", "subtitle": "count of labeled"},
        {"title": "Shape", "subtitle": "shape type"},
        {"title": "Color", "subtitle": "color of mask"},
        {"title": "Reason", "subtitle": "the reason the object is unavailable"},

    ]

    objects_project_meta = api.project.get_meta(id=project_id)

    rows = generate_rows_by_ann(objects_project_meta)

    pos_rows, neg_rows = split_rows(rows)

    state["classCountsMin"] = {
        row['Name']: 0 for row in rows
    }

    state["classCountsMax"] = {
        row['Name']: 0 for row in rows
    }

    for flag in ['Pos', 'Neg']:
        rows = pos_rows if flag == 'Pos' else neg_rows

        data[f"myColumns{flag}"] = pos_columns if flag == 'Pos' else neg_columns
        data[f"myRows{flag}"] = rows


        state[f"labeledImages{flag}"] = {
            row['Name']: 0 for row in rows
        }

        state[f"labeledObjects{flag}"] = {
            row['Name']: 0 for row in rows
        }

        state[f"reason{flag}"] = {
            row['Name']: 'invalid shape type' for row in rows
        }

    state["classIsPositive"] = {
        row['Name']: True for row in pos_rows
    }


def init_progress_bars(data, state):
    progress_names = ['DownloadAnnotations', 'DownloadBackgrounds', 'DownloadObjects',
                      'Preview', 'Synth', '4']

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

