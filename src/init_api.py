import os
import supervisely_lib as sly


TEAM_ID = int(os.environ['context.teamId'])
WORKSPACE_ID = int(os.environ['context.workspaceId'])
PROJECT_ID = int(os.environ["modal.state.slyProjectId"])

app = sly.AppService()
api: sly.Api = app.public_api
