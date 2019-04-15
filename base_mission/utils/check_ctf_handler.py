# -*- coding: utf-8 -*-
from base_mission.cms import serializers
from base_mission import constant
from base_mission.models import CTFMission, CheckMission
from .handle_func import get_target_fields
from base_monitor.models import Scripts

ctf_mission_fields = ['target', 'flag']
check_mission_fields = ['is_once', 'first_check_time', 'is_polling', 'interval', 'target', 'check_type', 'params',
                        'target_net', 'checker_id', 'scripts']


def save_ctf_or_check_mission(mission, data, update=False):
    mission_serializer = serializers.CTFSerializer if (
            mission.type == constant.Type.CTF) else serializers.CheckSerializer
    fields = ctf_mission_fields if (mission.type == constant.Type.CTF) else check_mission_fields
    submit_data = get_target_fields(data, fields=fields)

    if not update:
        submit_data.update({'mission': mission.pk})
        serializer = mission_serializer(data=submit_data)
    else:
        if mission.type == constant.Type.CTF:
            ctf_mission = CTFMission.objects.filter(mission=mission.id).first()
            if ctf_mission:
                serializer = mission_serializer(ctf_mission, data=submit_data, partial=True)
            else:
                submit_data.update({'mission': mission.pk})
                serializer = mission_serializer(data=submit_data)
        else:
            check_mission = CheckMission.objects.filter(mission=mission.id).first()
            if check_mission:
                serializer = mission_serializer(check_mission, data=submit_data, partial=True)
            else:
                submit_data.update({'mission': mission.pk})
                serializer = mission_serializer(data=submit_data)

    serializer.is_valid(raise_exception=True)
    serializer.save(mission=mission)


def get_remote_script_device(script=''):
    params = script.split('.')
    title = params[0]
    suffix = 0 if (params[-1] == 'py') else 1
    machine = Scripts.objects.get(title=title, suffix=suffix, type=1)
    if machine:
        return machine.checker_id
    return 0
