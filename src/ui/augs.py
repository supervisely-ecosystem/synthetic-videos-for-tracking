import os
import pickle
import random
import numpy

import cv2

from functions_objects import get_objects_list_for_project
from functions_video import add_object_to_background

import supervisely_lib as sly
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


def load_dumped(filename):
    load_path = os.path.join(app.data_dir, 'dumps', filename)
    with open(load_path, 'rb') as dumped:
        return pickle.load(dumped)


@app.callback("preview_base_augs")
@sly.timeit
# @app.ignore_errors_and_show_dialog_window()
def preview_augs(api: sly.Api, task_id, context, state, app_logger):
    augmentation_type = 'Base'

    gallery_template = CompareGallery(task_id, api, f"data.gallery{augmentation_type}1", project_meta)
    gallery_custom = CompareGallery(task_id, api, f"data.gallery{augmentation_type}2", project_meta)

    fields = [
        {"field": f"data.gallery{augmentation_type}1", "payload": gallery_template.to_json()},
        {"field": f"gallery{augmentation_type}2", "payload": gallery_custom.to_json()},
    ]
    api.app.set_fields(task_id, fields)

    # req_objects = load_dumped(state['req_objects'])
    req_objects = load_dumped('req_object.pkl')  # on debug
    req_backgrounds = load_dumped('req_backgrounds.pkl')  # on debug

    req_objects = req_objects[random.randint(0, len(req_objects)) - 1]
    req_backgrounds = req_backgrounds[random.randint(0, len(req_backgrounds)) - 1]

    if state[f"augs{augmentation_type}Type"] == "template":
        gallery = gallery_template
        augs_ppl = get_template_by_name(state[f"augs{augmentation_type}TemplateName"])
    else:
        gallery = gallery_custom
        augs_ppl = custom_pipeline

    temp_background = cv2.imread(req_backgrounds.image_path)
    temp_object = get_objects_list_for_project([req_objects])[0]
    temp_object.image = cv2.cvtColor(temp_object.image, cv2.COLOR_BGR2RGB)
    # temp_object.image = cv2.bitwise_and(temp_object.image, temp_object.image,
    #                                     mask=temp_object.mask.astype(numpy.uint8) * 255)

    center_of_background_x = (temp_background.shape[1] - temp_object.image.shape[1]) / 2
    center_of_background_y = (temp_background.shape[0] - temp_object.image.shape[0]) / 2

    class_lemon = sly.ObjClass('lemon', sly.Rectangle)

    # Label
    label_lemon = sly.Label(sly.Rectangle(center_of_background_y, center_of_background_x,
                                          center_of_background_y + temp_object.image.shape[1],
                                          center_of_background_x + temp_object.image.shape[0]), class_lemon)

    ann_own = sly.Annotation(temp_background.shape, [label_lemon], 'example annotaion')
    add_object_to_background(
        temp_background, temp_object)

    before_image_path = os.path.join(app.data_dir, "before_preview_augs.jpg")
    sly.image.write(before_image_path, temp_background)

    if api.file.exists(team_id, remote_preview_path.format('before')):
        api.file.remove(team_id, remote_preview_path.format('before'))
    file_info = api.file.upload(team_id, before_image_path, remote_preview_path.format('before'))
    gallery.set_left("before", file_info.full_storage_url, ann_own)

    _, res_img, res_ann = sly.imgaug_utils.apply(augs_ppl, project_meta, temp_object.image, ann_own)
    local_image_path = os.path.join(app.data_dir, "after_preview_augs.jpg")
    sly.image.write(local_image_path, res_img)
    if api.file.exists(team_id, remote_preview_path.format('after')):
        api.file.remove(team_id, remote_preview_path.format('after'))
    file_info = api.file.upload(team_id, local_image_path, remote_preview_path.format('after'))
    gallery.set_right("after", file_info.full_storage_url, res_ann)
    gallery.update(options=False)


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


def init(data, state):
    state["useAugs"] = True
    state["augsBaseType"] = "template"
    templates_info, name_to_py = get_aug_templates_list()
    data["augTemplates"] = templates_info
    data["augPythonCode"] = name_to_py
    state["augsBaseTemplateName"] = templates_info[0]["name"]

    data["pyViewOptions"] = {
        "mode": 'ace/mode/python',
        "showGutter": False,
        "readOnly": True,
        "maxLines": 100,
        "highlightActiveLine": False
    }

    state["customAugsPath"] = ""  # "/svs-heavy-no-fliplr.json"  # @TODO: for debug
    data["customAugsPy"] = None

    global galleryBase1, galleryBase2, \
        galleryMinor1, galleryMinor2, \
        galleryFrame1, galleryFrame2

    galleryBase1 = CompareGallery(task_id, api, "data.galleryBase1", project_meta)
    data["galleryBase1"] = galleryBase1.to_json()
    galleryBase2 = CompareGallery(task_id, api, "data.galleryBase2", project_meta)
    data["galleryBase2"] = galleryBase2.to_json()
    state["collapsed5"] = True
    state["disabled5"] = True
    data["done5"] = False


def restart(data, state):
    data["done5"] = False


@app.callback("load_existing_pipeline")
@sly.timeit
@app.ignore_errors_and_show_dialog_window()
def load_existing_pipeline(api: sly.Api, task_id, context, state, app_logger):
    global _custom_pipeline_path, custom_pipeline

    api.task.set_field(task_id, "data.customAugsPy", None)

    remote_path = state["customAugsPath"]
    _custom_pipeline_path = os.path.join(app.data_dir, sly.fs.get_file_name_with_ext(remote_path))
    api.file.download(team_id, remote_path, _custom_pipeline_path)

    custom_pipeline, py_code = _load_template(_custom_pipeline_path)
    api.task.set_field(task_id, "data.customAugsPy", py_code)


@app.callback("use_augs")
@sly.timeit
@app.ignore_errors_and_show_dialog_window()
def use_augs(api: sly.Api, task_id, context, state, app_logger):
    global augs_config_path

    if state["useAugs"] is True:
        augs_config_path = os.path.join(train_config.configs_dir, "augs_config.json")
        sly.json.dump_json_file(augs_json_config, augs_config_path)

        augs_py_path = os.path.join(train_config.configs_dir, "augs_preview.py")
        with open(augs_py_path, 'w') as f:
            f.write(augs_py_preview)
    else:
        augs_config_path = None

    fields = [
        {"field": "data.done5", "payload": True},
        {"field": "state.collapsed6", "payload": False},
        {"field": "state.disabled6", "payload": False},
        {"field": "state.activeStep", "payload": 6},
    ]
    api.app.set_fields(task_id, fields)
