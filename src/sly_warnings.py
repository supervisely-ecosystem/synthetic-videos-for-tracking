from sly_globals import *


def window_warner(message, fields):
    app.show_modal_window(message, level='warning')
    if len(fields) > 0:
        api.task.set_fields(task_id, fields)
