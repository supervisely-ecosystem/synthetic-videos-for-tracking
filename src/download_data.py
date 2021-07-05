from sly_globals import *

from sly_warnings import window_warner
from functools import partial

import math


objects_ann_info = None
backgrounds_ann_info = None


class SlyProgress:
    def __init__(self, api, task_id, pbar_element_name):
        self.api = api
        self.task_id = task_id
        self.pbar_element_name = pbar_element_name
        self.pbar = None

    def refresh_params(self, desc, total, is_size=False):
        self.pbar = sly.Progress(desc, total, is_size=is_size)
        # if total > 0:
        self.refresh_progress()
        # self.reset_params()

    def refresh_progress(self):
        curr_step = math.floor(self.pbar.current * 100 /
                   self.pbar.total) if self.pbar.total != 0 else 0

        fields = [
            {"field": f"data.{self.pbar_element_name}", "payload": curr_step},
            {"field": f"data.{self.pbar_element_name}Message", "payload": self.pbar.message},
            {"field": f"data.{self.pbar_element_name}Current", "payload": self.pbar.current},
            {"field": f"data.{self.pbar_element_name}Total", "payload": self.pbar.total},
        ]
        self.api.task.set_fields(self.task_id, fields)

    def reset_params(self):
        fields = [
            {"field": f"data.{self.pbar_element_name}", "payload": None},
            {"field": f"data.{self.pbar_element_name}Message", "payload": None},
            {"field": f"data.{self.pbar_element_name}Current", "payload": None},
            {"field": f"data.{self.pbar_element_name}Total", "payload": None},
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


class RequirementObject:
    def __init__(self, ds_id, image_id, is_tracking, annotation):
        self.ds_id = ds_id
        self.image_id = image_id
        self.is_tracking = is_tracking
        self.annotation = annotation


def get_project_ann_info(project_id, dataset_names=None, all_ds=False):
    sly_progress_ann = SlyProgress(api, task_id, 'progressDownloadAnnotations')
    sly_progress_ds = SlyProgress(api, task_id, 'progressDownloadAnnotationsDs')

    ann_infos = {}

    if all_ds:
        dataset_ids = [ds.id for ds in api.dataset.get_list(project_id)]
    else:
        dataset_ids = [ds.id for ds in api.dataset.get_list(project_id) if ds.name in dataset_names]

    sly_progress_ds.refresh_params('Current dataset', len(dataset_ids))
    for dataset_id in dataset_ids:
        sly_progress_ann.refresh_params('Downloading annotations',
                                        api.dataset.get_info_by_id(dataset_id).items_count)
        progress_cb = partial(sly_progress_ann.update_progress, api=api, task_id=task_id,
                              progress=sly_progress_ann.pbar)
        progress_cb(0)

        ann_infos[dataset_id] = api.annotation.get_list(dataset_id, progress_cb=progress_cb)

        sly_progress_ds.next_step()

    sly_progress_ann.reset_params()
    sly_progress_ds.reset_params()

    return ann_infos


def download_images(req_objects, subdir, sly_progress=None, need_reset_progress=True):
    if sly_progress:
        sly_progress.refresh_params(f"Downloading {subdir}", len(req_objects))

    root_dir = os.path.join(app.data_dir, subdir)

    for curr_object in req_objects:
        img_info = api.image.get_info_by_id(curr_object.image_id)
        dest_dir = os.path.join(root_dir, str(curr_object.ds_id))
        img_path = os.path.join(dest_dir, img_info.name)

        if not (os.path.exists(img_path)):
            api.image.download_path(curr_object.image_id, img_path)  # @TODO progressbar

        curr_object.image_path = img_path

        if sly_progress:
            sly_progress.next_step()

    if need_reset_progress and sly_progress:
        sly_progress.reset_params()


def get_list_req_objects(ann_data, state):
    needed_objects = []

    required_objects = state['classCountsMax']
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


def fill_tables_by_objects(state, objects_ann_info):

    for flag in ['Pos', 'Neg']:

        labels = state[f"labeledImages{flag}"].keys()

        labeled_images = {}
        labeled_objects = {}

        for curr_project in objects_ann_info.values():
            for annotation_info in curr_project:
                for object_info in annotation_info.annotation['objects']:
                    labeled_count = labeled_objects.get(object_info['classTitle'], 0)
                    labeled_count += 1
                    labeled_objects[object_info['classTitle']] = labeled_count

                    images_ids = labeled_images.get(object_info['classTitle'], [])
                    if annotation_info.image_id not in images_ids:
                        images_ids.append(annotation_info.image_id)
                        labeled_images[object_info['classTitle']] = images_ids

        labeled_images_count = {key: len(value) for key, value in labeled_images.items() if key in labels}
        labeled_objects_count = {key: value for key, value in labeled_objects.items() if key in labels}

        fields = [
            {"field": f"state.labeledImages{flag}", "payload": labeled_images_count, "append": True, "recursive": False},
            {"field": f"state.labeledObjects{flag}", "payload": labeled_objects_count, "append": True, "recursive": False},

        ]
        api.task.set_fields(task_id, fields)

    return 0


@app.callback("download_backgrounds_ann")
@sly.timeit
def download_backgrounds_ann(api: sly.Api, task_id, context, state, app_logger):
    sly_progress = SlyProgress(api, task_id, 'progressDownloadBackgrounds')
    sly_progress.refresh_params("Downloading meta", 1)
    backgrounds_ann_info = get_project_ann_info(project_id=state['bgProjectId'],
                                                dataset_names=state['bgDatasets'],
                                                all_ds=state['allDatasets'])

    sly_progress.next_step()
    sly_progress.reset_params()

    req_backgrounds = get_list_req_backgrounds(backgrounds_ann_info, state)
    dump_req(req_backgrounds, 'req_backgrounds.pkl')

    # @TODO resizing dialog window
    # if not objects_larger_than_backgrounds(req_objects, req_backgrounds):

    fields = [
        {"field": "state.step3Loading", "payload": False},
        {"field": "state.done3", "payload": True},
        {"field": "state.activeStep", "payload": 4},
        {"field": "state.collapsed4", "payload": False},
        {"field": "state.disabled4", "payload": False},

    ]
    api.task.set_fields(task_id, fields)
    api.app.set_field(task_id, "data.scrollIntoView", f"step{4}")
    # else:
    #     fields = [
    #         {"field": "state.showCanResizeWindow", "payload": True},
    #         {"field": "state.step2Loading", "payload": False},
    #     ]
    #
    #     api.task.set_fields(task_id, fields)




@app.callback("download_objects")
@sly.timeit
@app.ignore_errors_and_show_dialog_window()
def download_objects(api: sly.Api, task_id, context, state, app_logger):
    sly_progress = SlyProgress(api, task_id, 'progressDownloadObjects')

    req_objects = get_list_req_objects(objects_ann_info, state)

    if len(req_objects) == 0:
        window_warner(message=f"No objects selected.\nPlease select objects.",
                      fields=[{"field": "state.step2Loading", "payload": False}])

    else:

        # req_backgrounds = load_dumped('req_backgrounds.pkl')

        download_images(req_objects, 'objects', sly_progress)

        dump_req(req_objects, 'req_objects.pkl')

        fields = [
            {"field": "state.step2Loading", "payload": False},
            {"field": "state.done2", "payload": True},
            {"field": "state.activeStep", "payload": 3},
            {"field": "state.collapsed3", "payload": False},
            {"field": "state.disabled3", "payload": False},

        ]
        api.app.set_field(task_id, "data.scrollIntoView", f"step{3}")

        api.task.set_fields(task_id, fields)

# @TODO use this function to allow resizin
# @app.callback("define_resize_status")
# @sly.timeit
# def define_resize_status(api: sly.Api, task_id, context, state, app_logger):
#     can_resize = state['canResize']
# 
#     if can_resize:
#         fields = [
#             {"field": "state.done3", "payload": True},
#             {"field": "state.activeStep", "payload": 4},
#             {"field": "state.collapsed4", "payload": False},
#             {"field": "state.disabled4", "payload": False},
#             {"field": "state.showCanResizeWindow", "payload": False},
# 
#         ]
#         api.app.set_field(task_id, "data.scrollIntoView", f"step{4}")
# 
#         api.task.set_fields(task_id, fields)
# 
#     else:
#         fields = [
#             {"field": "state.showCanResizeWindow", "payload": False},
#         ]
#         window_warner('Please reselect objects or backgrounds', [])
# 
#         api.task.set_fields(task_id, fields)


@app.callback("download_objects_annotations")
@sly.timeit
@app.ignore_errors_and_show_dialog_window()
def download_objects_annotations(api: sly.Api, task_id, context, state, app_logger):
    ann_info = get_project_ann_info(project_id=project_id,
                                            dataset_names=None,
                                            all_ds=True)
    global objects_ann_info

    objects_ann_info = ann_info

    fields = [
        {"field": "state.step1Loading", "payload": False},
        {"field": "state.done1", "payload": True},
        {"field": "state.activeStep", "payload": 2},
        {"field": "state.collapsed2", "payload": False},
        {"field": "state.disabled2", "payload": False},

    ]
    api.task.set_fields(task_id, fields)
    api.app.set_field(task_id, "data.scrollIntoView", f"step{2}")


@app.callback("load_objects_stats")
@sly.timeit
@app.ignore_errors_and_show_dialog_window()
def load_objects_stats(api: sly.Api, task_id, context, state, app_logger):
    global objects_ann_info
    fill_tables_by_objects(state, objects_ann_info)

    fields = [
        {"field": "state.step2StatsLoading", "payload": False},
        {"field": "state.loadStats", "payload": True},

    ]
    api.task.set_fields(task_id, fields)

