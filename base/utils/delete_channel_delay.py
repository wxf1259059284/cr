# -*- coding: UTF-8 -*-
import json

from channels.delay import models as delay_models
import ast


def delete_channel_delay(content):
    delay_tasks = delay_models.DelayedMessage.objects.all()
    for delay_task in delay_tasks:
        if len(content) == 0 or type(content) != dict:
            return False

        key = content.keys()[0]

        try:
            delay_task_content = json.loads(delay_task.content)
        except Exception:
            delay_task_content = ast.literal_eval(delay_task.content)

        if type(delay_task_content) != dict:
            return False

        if key in delay_task_content and key in content:
            if delay_task_content[key] == content[key]:
                delay_task.delete()
