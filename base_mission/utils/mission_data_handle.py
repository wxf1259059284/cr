# -*- coding: utf-8 -*-
import os
import shutil

from base.utils.thread import async_exe
from base_mission import constant
from base_mission.utils.exam_tasks_handler import create_update_tasks
from base_mission.utils.check_ctf_handler import save_ctf_or_check_mission
from cr import settings


def save_related_mission(mission, data, update=False):
    if mission.type in [constant.Type.CTF, constant.Type.CHECK]:
        save_ctf_or_check_mission(mission, data, update=update)
    elif mission.type == constant.Type.EXAM:
        create_update_tasks(mission, data)

    if mission.type == constant.Type.CHECK:
        async_exe(mission_copy_file, (mission, data,), delay=0)


def mission_copy_file(mission, data):
    if not hasattr(mission, "id"):
        raise Exception('No id attribute')

    mission_script_dir = os.path.join(settings.MEDIA_ROOT, 'scripts/mission/{}/').format(mission.id)

    if not os.path.exists(mission_script_dir):
        os.makedirs(mission_script_dir)

    if data.get("scripts", None):
        script = data.get("scripts")
    else:
        return False

    if "check_type" in data:
        check_type = data.get("check_type")
    else:
        return False

    if check_type == 0:
        script_path = os.path.join(settings.MEDIA_ROOT, 'scripts/remote/{}').format(script)
    elif check_type == 1:
        script_path = os.path.join(settings.MEDIA_ROOT, 'scripts/local/{}').format(script)
    else:
        raise Exception('No script file')

    if not os.path.exists(script_path):
        raise Exception('No script file')
    else:
        mission_script_path = os.path.join(mission_script_dir, '{}').format(script)
        try:
            shutil.copyfile(script_path, mission_script_path)
        except Exception as e:
            raise Exception('An error occurred :%s', e)
