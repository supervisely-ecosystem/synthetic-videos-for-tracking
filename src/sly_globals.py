import os
from pathlib import Path
import sys
import supervisely as sly
from supervisely.app.v1.app_service import AppService
import pickle


app = AppService()
api = app.public_api
task_id = app.task_id

team_id = int(os.environ['context.teamId'])
workspace_id = int(os.environ['context.workspaceId'])
project_id = int(os.environ['modal.state.slyProjectId'])

project_info = api.project.get_info_by_id(project_id)
if project_info is None:  # for debug
    raise ValueError(f"Project with id={project_id} not found")

#sly.fs.clean_dir(app.data_dir)  # @TODO: for debug

project_meta = sly.ProjectMeta.from_json(api.project.get_meta(project_id))

artifacts_dir = os.path.join(app.data_dir, "artifacts")
sly.fs.mkdir(artifacts_dir)
info_dir = os.path.join(artifacts_dir, "info")
sly.fs.mkdir(info_dir)
checkpoints_dir = os.path.join(artifacts_dir, "checkpoints")
sly.fs.mkdir(checkpoints_dir)

root_source_dir = str(Path(sys.argv[0]).parents[1])

sly.logger.info(f"Root source directory: {root_source_dir}")
sys.path.append(root_source_dir)
source_path = str(Path(sys.argv[0]).parents[0])
sly.logger.info(f"App source directory: {source_path}")
sys.path.append(source_path)
ui_sources_dir = os.path.join(source_path, "ui")
sly.logger.info(f"UI source directory: {ui_sources_dir}")
sys.path.append(ui_sources_dir)
sly.logger.info(f"Added to sys.path: {ui_sources_dir}")


def dump_req(req_objects, filename):
    save_path = os.path.join(app.data_dir, 'dumps')
    os.makedirs(save_path, exist_ok=True)
    save_path = os.path.join(save_path, filename)
    with open(save_path, 'wb') as dump_file:
        pickle.dump(req_objects, dump_file)


def load_dumped(filename):
    load_path = os.path.join(app.data_dir, 'dumps', filename)
    with open(load_path, 'rb') as dumped:
        return pickle.load(dumped)
