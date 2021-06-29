from sly_globals import *
import shutil
import random
import json
import pickle

from init_ui import *
from functions_background import *
from sly_warnings import window_warner


class RequirementObject:
    def __init__(self, ds_id, image_id, is_tracking, annotation):
        self.ds_id = ds_id
        self.image_id = image_id
        self.is_tracking = is_tracking
        self.annotation = annotation




def get_project_ann_info(project_id, dataset_names=None, all_ds=False):
    ann_infos = {}

    if all_ds:
        dataset_ids = [ds.id for ds in api.dataset.get_list(project_id)]
    else:
        dataset_ids = [ds.id if ds.name in dataset_names else None for ds in api.dataset.get_list(project_id)]

    for dataset_id in dataset_ids:
        if dataset_id:
            ann_infos[dataset_id] = api.annotation.get_list(dataset_id)

    return ann_infos



def download_images(req_objects, subdir, sly_progress):

    sly_progress.refresh_params(f"Downloading {subdir}", len(req_objects))
    root_dir = os.path.join(app.data_dir, subdir)

    for curr_object in req_objects:
        img_info = api.image.get_info_by_id(curr_object.image_id)
        dest_dir = os.path.join(root_dir, str(curr_object.ds_id))
        img_path = os.path.join(dest_dir, img_info.name)

        if not (os.path.exists(img_path)):
            api.image.download_path(curr_object.image_id, img_path)  # @TODO progressbar

        curr_object.image_path = img_path

        sly_progress.next_step()


def get_list_req_objects(ann_data, state):
    needed_objects = []

    required_objects = state['classCounts']
    is_tracking = state["classIsPositive"]

    for req_object_label, count in required_objects.items():
        if count == 0:
            continue

        temp_count = 0

        for (ds_id, ds_ann_info) in ann_data.items():
            for image_ann_info in ds_ann_info:

                for curr_object in image_ann_info.annotation['objects']:
                    if req_object_label == curr_object['classTitle']:
                        ann_copy = image_ann_info.annotation.copy()
                        ann_copy['objects'] = [curr_object]
                        needed_objects.append(RequirementObject(ds_id=ds_id,
                                                                image_id=image_ann_info.image_id,
                                                                is_tracking=is_tracking[f'{req_object_label}'],
                                                                annotation=ann_copy))
                        temp_count += 1

                    if temp_count == count:
                        break

                if temp_count == count:
                    break

    return needed_objects


def get_list_req_backgrounds(backgrounds_ann_info, state):
    req_backgrounds = []

    for ds_id, ann_info in backgrounds_ann_info.items():
        for curr_image in ann_info:
            req_backgrounds.append(RequirementObject(ds_id=ds_id,
                                                     image_id=curr_image.image_id,
                                                     is_tracking=None,
                                                     annotation=None))

    return req_backgrounds


@app.callback("download_backgrounds")
@sly.timeit
def download_project(api: sly.Api, task_id, context, state, app_logger):
    sly_progress = SlyProgress(api, task_id, 'progressDownloadBackgrounds')
    sly_progress.refresh_params("Downloading meta", 1)
    backgrounds_ann_info = get_project_ann_info(project_id=state['bgProjectId'],
                                                dataset_names=state['bgDatasets'],
                                                all_ds=state['allDatasets'])

    sly_progress.next_step()

    req_backgrounds = get_list_req_backgrounds(backgrounds_ann_info, state)
    download_images(req_backgrounds, 'backgrounds', sly_progress)
    dump_req(req_backgrounds, 'req_backgrounds.pkl')

    fields = [
        {"field": "state.step1Loading", "payload": False},
        {"field": "state.done1", "payload": True},
        {"field": "state.activeStep", "payload": 2},
        {"field": "state.collapsed2", "payload": False},
        {"field": "state.disabled2", "payload": False},

    ]
    api.task.set_fields(task_id, fields)
    api.app.set_field(task_id, "data.scrollIntoView", f"step{2}")


@app.callback("download_objects")
@sly.timeit
# @app.ignore_errors_and_show_dialog_window()
def download_project(api: sly.Api, task_id, context, state, app_logger):

    sly_progress = SlyProgress(api, task_id, 'progressDownloadObjects')

    sly_progress.refresh_params("Downloading annotations", 1)

    objects_ann_info = get_project_ann_info(project_id=project_id,
                                            dataset_names=None,
                                            all_ds=True)

    sly_progress.next_step()

    req_objects = get_list_req_objects(objects_ann_info, state)

    if len(req_objects) == 0:
        window_warner(message=f"No objects selected.\nPlease select objects.",
                      fields=[{"field": "state.step2Loading", "payload": False}])

    else:

        req_backgrounds = load_dumped('req_backgrounds.pkl')

        download_images(req_objects, 'objects', sly_progress)

        dump_req(req_objects, 'req_object.pkl')

        if not objects_larger_than_backgrounds(req_objects, req_backgrounds):

            fields = [
                {"field": "state.step2Loading", "payload": False},
                {"field": "state.done2", "payload": True},
                {"field": "state.activeStep", "payload": 3},
                {"field": "state.collapsed3", "payload": False},
                {"field": "state.disabled3", "payload": False},

            ]
            api.app.set_field(task_id, "data.scrollIntoView", f"step{3}")

            api.task.set_fields(task_id, fields)

        else:
            fields = [
                {"field": "state.showCanResizeWindow", "payload": True},
                {"field": "state.step2Loading", "payload": False},
            ]

            api.task.set_fields(task_id, fields)


@app.callback("define_resize_status")
@sly.timeit
def define_resize_status(api: sly.Api, task_id, context, state, app_logger):
    can_resize = state['canResize']

    if can_resize:
        fields = [
            {"field": "state.done2", "payload": True},
            {"field": "state.activeStep", "payload": 3},
            {"field": "state.collapsed3", "payload": False},
            {"field": "state.disabled3", "payload": False},
            {"field": "state.showCanResizeWindow", "payload": False},

        ]
        api.app.set_field(task_id, "data.scrollIntoView", f"step{3}")

        api.task.set_fields(task_id, fields)

    else:
        fields = [
            {"field": "state.showCanResizeWindow", "payload": False},
        ]
        window_warner('Please reselect objects', [])

        api.task.set_fields(task_id, fields)
