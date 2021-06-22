import os
import supervisely_lib as sly


def init_input_project(api: sly.Api, data: dict, project_info):
    data["projectId"] = project_info.id
    data["projectName"] = project_info.name
    data["projectPreviewUrl"] = api.image.preview_url(project_info.reference_image_url, 100, 100)
    data["projectItemsCount"] = project_info.items_count


def init_settings(state):

    state["bgTeamId"] = None
    state["bgWorkspaceId"] = None
    state["bgProjectId"] = None
    state["bgDatasets"] = None
    state["allDatasets"] = True

    state["speedInterval"] = [5, 20]
    state["linearLaw"] = True
    state["randomLaw"] = True
    state["fps"] = 25

    state["durationPreview"] = 1
    state["durationVideo"] = 60


def init_res_project(data, state, project_info):
    data["resProjectId"] = None
    state["resProjectName"] = f"synthesized_{project_info.name}_{state['fps']}fps"
    data["resProjectName"] = None
    data["resProjectPreviewUrl"] = None
    data["started"] = False


