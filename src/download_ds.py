from init_api import *
import shutil


def download_project(project_id, dataset_ids=None, all_ds=False, subdir=''):
    project_info = api.project.get_info_by_id(project_id)
    dest_dir = os.path.join(app.data_dir, subdir)

    if os.path.exists(dest_dir):  # check if path exists
        shutil.rmtree(dest_dir)

    if all_ds:
        dataset_ids = [ds.id for ds in api.dataset.get_list(project_id)]

    sly.download_project(api, project_info.id, dest_dir, dataset_ids=dataset_ids, log_progress=True)

    print(f'{project_id} downloaded')
