# -*- coding: utf-8 -*-
from rest_framework import exceptions
from base_mission.models import ExamTask, Mission
from base_mission.cms.serializers import ExamTaskSerializer
from base_mission import constant
from .handle_func import save_options, get_target_fields

exam_task_fields = ['task_title', 'task_content', 'task_score', 'task_type', 'answer', 'task_index']
exam_task_func_fields = {'option': save_options}

required_fields = ['task_title', 'task_content', 'answer']


def createUpdateExamTask(data, exam, isUpdate=False, existId=None):
    if isUpdate:
        exam_task = ExamTask.objects.filter(id=existId).first()
        serializer = ExamTaskSerializer(exam_task, data=data, partial=True)
    else:
        serializer = ExamTaskSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save(exam=exam)


def create_update_tasks(mission, data):
    exist_tasks = ExamTask.objects.filter(exam_id=mission.id).order_by('task_index')
    exam = Mission.objects.get(id=mission.id)

    request_tasks = []
    task_list = data.get('examtasks')
    if not task_list:
        raise exceptions.ValidationError('Empty Task List')

    for task in task_list:
        request_tasks.append(get_target_fields(task, fields=exam_task_fields, func_fields=exam_task_func_fields))

    title_list = [task.get('task_title') for task in request_tasks]
    if len(set(title_list)) != len(title_list):
        raise exceptions.ValidationError('Duplicate Task Title')

    len_old = len(exist_tasks)
    len_new = len(request_tasks)

    if len_new == len_old:
        for index, task_data in enumerate(request_tasks):
            createUpdateExamTask(data=task_data, exam=exam, isUpdate=True, existId=exist_tasks[index].id)

    elif len_new > len_old:
        for index, task in enumerate(exist_tasks):
            createUpdateExamTask(data=request_tasks[index], exam=exam, isUpdate=True, existId=task.id)

        for num in range(len_old, len_new):
            extra_data = {
                'exam': mission.id,
                'task_index': num,
            }
            request_tasks[num].update(extra_data)
            createUpdateExamTask(data=request_tasks[num], exam=exam)

    else:
        for index, task in enumerate(request_tasks):
            createUpdateExamTask(data=task, exam=exam, isUpdate=True, existId=exist_tasks[index].id)

        update_list = []
        for num in range(len_new, len_old):
            update_list.append(exist_tasks[num].id)

        ExamTask.objects.filter(id__in=update_list).update(status=constant.Status.DELETE)
