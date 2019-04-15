# -*- coding: utf-8 -*-
import json

from django.core.cache import cache
from rest_framework import exceptions

from base.utils.enum import Enum
from cr_scene.error import error
from cr_scene.models import CrEventScene, CrScene

MISSIONSTATUS = Enum(
    NOTDONE=0,
    FAILE=1,
    SUCCESS=2,
)


def get_missions_data(queryset, serializer, **kwargs):
    data_dict = {}
    for instance in queryset:
        if hasattr(instance, 'ctfmission'):
            data = serializer.CTFMissionSerializer(instance).data
        elif hasattr(instance, 'checkmission'):
            data = serializer.CheckMissionSerializer(instance).data
        else:
            data = {}
        if data and 'user_submit_status' in kwargs:
            data.update({'user_submit_status': kwargs.get('user_submit_status')})
        data_dict[instance.id] = data
    return data_dict


def serializer_mission_data_web(data):
    return data


def check_mission_answer_exam_task_get_all_score(answer, exam_tasks):
    # 考试型任务一次就算完成, 看自己能得多少分
    if isinstance(answer, str):
        answer = json.loads(answer)
    all_task_score = score = 0
    is_solved = False
    for exam_task in exam_tasks:
        all_task_score += exam_task.task_score
        user_submit_answer = answer[str(exam_task.id)]
        right_answer = "|".join(exam_task.answer)
        flag = check_mission_answer_by_one(user_submit_answer, right_answer)
        if flag is True:
            score += exam_task.task_score
    if score == all_task_score:
        is_solved = True
    is_solved = True
    return is_solved, score


def check_mission_answer_by_one(answer, right_answer):
    if answer is None or answer == '':
        return False
    answer_list = right_answer.split('|')
    web_answer_list = answer.split('|')
    if len(answer_list) != len(web_answer_list):
        return False
    for web_answer in web_answer_list:
        if web_answer in answer_list:
            answer_list.remove(web_answer)
    if len(answer_list) != 0:
        return False
    return True


def check_mission_answer(answer, mission):
    score = mission.score
    if mission.type == mission.Type.EXAM:
        flag, score = check_mission_answer_exam_task_get_all_score(answer, mission.examtask_set.all())
    elif mission.type == mission.Type.CTF:
        flag = check_mission_answer_by_one(answer, mission.ctfmission.flag)
        if flag is False:
            score = 0
    elif mission.type == mission.Type.CHECK:
        raise exceptions.ValidationError(error.CHECK_NOT_COMMIT)
    else:
        raise exceptions.ValidationError('目前只支持考试， ctf')
    return flag, score


def check_mission_has_down(submit_log_obj, mission):
    if mission.type == mission.Type.EXAM and submit_log_obj:
        raise exceptions.ValidationError(error.HAS_DOWN)
    if mission.type != mission.Type.EXAM and submit_log_obj.filter(is_solved=True):
        raise exceptions.ValidationError(error.HAS_DOWN)


def mapping_add_data(data_list, data_maping, has_answer=False, default_solved=False):
    for data in data_list:
        id = data['mission_id']
        if default_solved:
            data['is_solved'] = default_solved

        if id in data_maping.keys():
            data_maping[id].update({
                'user_submit_status': data['is_solved'] and MISSIONSTATUS.SUCCESS or MISSIONSTATUS.FAILE,
            })
            if has_answer:
                data_maping[id].update({
                    'user_submit_answer': data['answer']
                })
            if 'score' in data:
                data_maping[id].update({
                    'user_score': data['score']
                })

    return data_maping


def get_info_from_administrator_permission(request, obj):
    _permission_scene_ids = request.data.get('_permission_scene_ids')
    _permission_cr_event_scene_data = request.data.get('_permission_cr_event_scene_data')
    cr_event_scene_objs_mapping = {_permission_cr_event_scene['cr_scene_data']['id']: _permission_cr_event_scene for
                                   _permission_cr_event_scene in _permission_cr_event_scene_data}

    crscene_objs = obj.cr_scenes.filter(id__in=_permission_scene_ids)
    return crscene_objs, cr_event_scene_objs_mapping


def list_dict_as_only_one_key_to_new_dict(data_list, key):
    data_list = filter(lambda data: isinstance(data, dict) and key in data, data_list)
    new_data = {data[key]: data for data in data_list}
    return new_data


def get_deep_dict_value_as_key(data_dict):
    data = {}
    if not isinstance(data_dict, dict):
        return {}

    for key, values in data_dict.items():
        if isinstance(values, dict):
            for sub_key, sub_value in values.items():
                data[sub_value] = {
                    'machine_id': key,
                    'user_id': int(sub_key),
                }
    return data


def get_cr_scene_name(scene_id):
    data = cache.get('cr_scene_%d_name' % scene_id)
    if data:
        return data
    default_log_name = 'default'
    cr_event = CrEventScene.objects.filter(cr_scene_instance=scene_id).first()
    if cr_event:
        log_name = cr_event.cr_event.name if cr_event.cr_event else default_log_name
    else:
        scene = CrScene.objects.filter(scene_id=scene_id).first()
        log_name = scene.name if scene else default_log_name

    cache.set('cr_scene_%d_name' % scene_id, log_name, 60 * 60)
    return log_name
