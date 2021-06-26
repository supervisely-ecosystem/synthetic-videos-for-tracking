import os
import pickle
import random
import numpy

import cv2

from functions_objects import get_objects_list_for_project
from movement_controller import find_mask_tight_bbox

from sly_globals import *

from supervisely_lib.app.widgets import CompareGallery

_templates = [
    {
        "config": "src/augs/svs-lite.json",
        "name": "Lite (color + rotate)",
    },
    {
        "config": "src/augs/svs-lite-with-fliplr.json",
        "name": "Lite + fliplr",
    },
    {
        "config": "src/augs/svs-heavy-no-fliplr.json",
        "name": "Heavy",
    },
    {
        "config": "src/augs/svs-heavy-with-fliplr.json",
        "name": "Heavy + fliplr",
    },
]

_custom_pipeline_path = None
custom_pipeline = None

remote_preview_path = "/temp/{}_preview_augs.jpg"

augs_json_config = None
augs_py_preview = None
augs_config_path = None



@app.callback("base_augs_handler")
@sly.timeit
@app.ignore_errors_and_show_dialog_window()
def base_augs_handler(api: sly.Api, task_id, context, state, app_logger):
    preview_augs(state, 'Base')


@app.callback("minor_augs_handler")
@sly.timeit
@app.ignore_errors_and_show_dialog_window()
def base_augs_handler(api: sly.Api, task_id, context, state, app_logger):
    preview_augs(state, 'Minor')


@app.callback("frame_augs_handler")
@sly.timeit
# @app.ignore_errors_and_show_dialog_window()
def base_augs_handler(api: sly.Api, task_id, context, state, app_logger):
    preview_augs(state, 'Frame')




def preview_augs(state, augmentation_type):
    gallery_template = CompareGallery(task_id, api, f"data.gallery{augmentation_type}1", project_meta)
    gallery_custom = CompareGallery(task_id, api, f"data.gallery{augmentation_type}2", project_meta)

    gallery_template._options["syncViews"] = False
    gallery_template._options["enableZoom"] = False
    gallery_template._options["opacity"] = 0.2
    gallery_custom._options["syncViews"] = False
    gallery_custom._options["enableZoom"] = False
    gallery_custom._options["opacity"] = 0.2

    fields = [
        {"field": f"data.gallery{augmentation_type}1", "payload": gallery_template.to_json()},
        {"field": f"data.gallery{augmentation_type}2", "payload": gallery_custom.to_json()},
    ]
    api.app.set_fields(task_id, fields)

    req_objects = load_dumped(state['req_objects'])
    # req_objects = load_dumped('req_object.pkl')  # on debug

    if augmentation_type == 'Frame':
        req_objects = load_dumped(state['req_objects'])
        # req_objects = load_dumped('req_backgrounds.pkl')  # on debug

    req_objects = req_objects[random.randint(0, len(req_objects)) - 1]

    if state[f"augs{augmentation_type}Type"] == "template":
        gallery = gallery_template
        augs_ppl = get_template_by_name(state[f"augs{augmentation_type}TemplateName"])
    else:
        gallery = gallery_custom
        augs_ppl = custom_pipeline

    if augmentation_type == 'Frame':
        image, ann = get_frame_image(req_objects)
        ann = sly.Annotation(image.shape)
    else:
        image, ann = get_image_and_ann(req_objects)

    before_image_path = os.path.join(app.data_dir, "before_preview_augs.jpg")
    sly.image.write(before_image_path, image)
    if api.file.exists(team_id, remote_preview_path.format('before')):
        api.file.remove(team_id, remote_preview_path.format('before'))
    file_info = api.file.upload(team_id, before_image_path, remote_preview_path.format('before'))
    gallery.set_left(f"before shape: [{image.shape[1]}x{image.shape[0]}]",
                     file_info.full_storage_url, ann)

    _, res_img, res_ann = sly.imgaug_utils.apply(augs_ppl, project_meta, image, ann)

    if augmentation_type != 'Frame':
        res_mask = res_ann.labels[0].geometry.data

        t, l, b, r = find_mask_tight_bbox(res_mask)

        div_x = res_ann.labels[0].geometry.origin.col
        div_y = res_ann.labels[0].geometry.origin.row

        image_aug = res_img[div_y + t:div_y + b, div_x + l:div_x + r]
        mask_aug = res_mask[t:b, l:r]

        res_ann = res_ann.relative_crop(
            sly.Rectangle(div_y + t, div_x + l, div_y + b, div_x + r))
        #
        res_img = cv2.bitwise_and(image_aug, image_aug,
                                  mask=mask_aug.astype(numpy.uint8) * 255)

    local_image_path = os.path.join(app.data_dir, "after_preview_augs.jpg")
    sly.image.write(local_image_path, res_img)
    if api.file.exists(team_id, remote_preview_path.format('after')):
        api.file.remove(team_id, remote_preview_path.format('after'))
    file_info = api.file.upload(team_id, local_image_path, remote_preview_path.format('after'))
    gallery.set_right(f"after shape: [{res_img.shape[1]}x{res_img.shape[0]}]", file_info.full_storage_url, res_ann)
    gallery.update(options=False)


def get_frame_image(req_objects):
    image_path = req_objects.image_path
    image = cv2.imread(image_path)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB), None


def get_image_and_ann(req_objects):
    temp_object = get_objects_list_for_project([req_objects])[0]
    temp_object.image = cv2.cvtColor(temp_object.image, cv2.COLOR_BGR2RGB)
    temp_object.image = cv2.bitwise_and(temp_object.image, temp_object.image,
                                        mask=temp_object.mask.astype(numpy.uint8) * 255)

    div_x = temp_object.sly_ann.labels[0].geometry.origin.col
    div_y = temp_object.sly_ann.labels[0].geometry.origin.row

    ann = temp_object.sly_ann
    ann = ann.relative_crop(
        sly.Rectangle(div_y, div_x, div_y + temp_object.image.shape[0] - 1, div_x + temp_object.image.shape[1] - 1))

    return temp_object.image, ann


def _load_template(json_path):
    config = sly.json.load_json_file(json_path)
    pipeline = sly.imgaug_utils.build_pipeline(config["pipeline"], random_order=config["random_order"])  # to validate
    py_code = sly.imgaug_utils.pipeline_to_python(config["pipeline"], config["random_order"])

    global augs_json_config, augs_py_preview
    augs_json_config = config
    augs_py_preview = py_code

    return pipeline, py_code


def get_aug_templates_list():
    pipelines_info = []
    name_to_py = {}
    for template in _templates:
        json_path = os.path.join(root_source_dir, template["config"])
        _, py_code = _load_template(json_path)
        pipelines_info.append({
            **template,
            "py": py_code
        })
        name_to_py[template["name"]] = py_code
    return pipelines_info, name_to_py


def get_template_by_name(name):
    for template in _templates:
        if template["name"] == name:
            json_path = os.path.join(root_source_dir, template["config"])
            pipeline, _ = _load_template(json_path)
            return pipeline
    raise KeyError(f"Template \"{name}\" not found")


def init_augs(data, state):
    templates_info, name_to_py = get_aug_templates_list()

    data["augTemplates"] = templates_info
    data["augPythonCode"] = name_to_py

    data["pyViewOptions"] = {
        "mode": 'ace/mode/python',
        "showGutter": False,
        "readOnly": True,
        "maxLines": 100,
        "highlightActiveLine": False
    }
    for aug_type in ['Base', 'Minor', 'Frame']:
        state[f'use{aug_type}Augs'] = False
        state[f"augs{aug_type}Type"] = "template"

        state[f"augs{aug_type}TemplateName"] = templates_info[0]["name"]
        state[f"custom{aug_type}AugsPath"] = ""  # "/svs-heavy-no-fliplr.json"  # @TODO: for debug
        data[f"custom{aug_type}AugsPy"] = None

        gallery_template = CompareGallery(task_id, api, f"data.gallery{aug_type}1", project_meta)
        data[f"gallery{aug_type}1"] = gallery_template.to_json()

        gallery_custom = CompareGallery(task_id, api, f"data.gallery{aug_type}2", project_meta)
        data[f"gallery{aug_type}2"] = gallery_custom.to_json()


def restart(data, state):
    data["done2"] = False

#
# @app.callback("load_existing_pipeline")
# @sly.timeit
# @app.ignore_errors_and_show_dialog_window()
# def load_existing_pipeline(api: sly.Api, task_id, context, state, app_logger):
#     global _custom_pipeline_path, custom_pipeline
#
#     api.task.set_field(task_id, "data.customAugsPy", None)
#
#     remote_path = state["customAugsPath"]
#     _custom_pipeline_path = os.path.join(app.data_dir, sly.fs.get_file_name_with_ext(remote_path))
#     api.file.download(team_id, remote_path, _custom_pipeline_path)
#
#     custom_pipeline, py_code = _load_template(_custom_pipeline_path)
#     api.task.set_field(task_id, "data.customAugsPy", py_code)


@app.callback("apply_augs")
@sly.timeit
@app.ignore_errors_and_show_dialog_window()
def use_augs(api: sly.Api, task_id, context, state, app_logger):
    applied_augs = {}

    for aug_type in ['Base', 'Minor', 'Frame']:

        if state[f'use{aug_type}Augs']:
            applied_augs[aug_type] = get_template_by_name(state[f"augs{aug_type}TemplateName"])
        else:
            applied_augs[aug_type] = None

    dump_req(applied_augs, 'augmentations.pkl')

    fields = [
        {"field": "data.done2", "payload": True},
        {"field": "state.collapsed2", "payload": True},
        {"field": "state.collapsed3", "payload": False},
        {"field": "state.disabled2", "payload": True},
        {"field": "state.disabled3", "payload": False},
        {"field": "state.activeStep", "payload": 3},
        {"field": "state.augmentations", "payload": 'augmentations.pkl'}
    ]
    api.app.set_fields(task_id, fields)
