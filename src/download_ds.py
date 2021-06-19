from init_api import *

project_info = api.project.get_info_by_id(PROJECT_ID)
dataset_ids = [ds.id for ds in api.dataset.get_list(PROJECT_ID)]
dest_dir = os.path.join(my_app.data_dir, f'{project_info.id}_{project_info.name}')
sly.download_project(api, project_info.id, dest_dir, dataset_ids=dataset_ids, log_progress=True)
