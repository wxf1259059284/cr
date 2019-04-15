# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from base.utils.models.manager import MManager
from base_auth.models import User

from base_mission import constant


class Mission(models.Model):
    Type = constant.Type
    Status = constant.Status
    Difficulty = constant.Difficulty
    MissionStatus = constant.MissionStatus

    type = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    content = models.CharField(max_length=100, null=True, blank=True)
    score = models.IntegerField()
    status = models.IntegerField(default=Status.NORMAL)
    public = models.BooleanField(default=False)
    difficulty = models.IntegerField(default=Difficulty.INTRODUCTION)
    mission_status = models.IntegerField(default=MissionStatus.COMMING)
    create_time = models.DateTimeField(auto_now_add=True)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='mission_create_user', null=True,
                                    default=None)
    last_edit_user = models.ForeignKey(User, default=None, on_delete=models.SET_NULL, null=True,
                                       related_name='mission_last_edit_user')
    last_edit_time = models.DateTimeField(auto_now=True)

    # instance
    period = models.IntegerField()

    # position
    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()

    def __unicode__(self):
        return '%s' % self.title


class CTFMission(models.Model):
    mission = models.OneToOneField(Mission, primary_key=True)
    target = models.CharField(max_length=100)
    flag = models.CharField(max_length=1024)


class CheckMission(models.Model):
    CheckType = constant.CheckType

    mission = models.OneToOneField(Mission, primary_key=True)
    check_type = models.IntegerField(default=CheckType.SYSTEM)
    checker_id = models.CharField(max_length=100, default='', null=True)
    target_net = models.CharField(max_length=100, default='', null=True, blank=True)
    target = models.CharField(max_length=100)  # 靶机
    scripts = models.CharField(max_length=1024)
    is_once = models.BooleanField(default=False)  # 默认检测一次
    first_check_time = models.IntegerField(default=0)  # 首次检测时间，基于场景创建完成时间
    is_polling = models.BooleanField(default=False)  # 默认不轮询
    interval = models.IntegerField(default=0, null=True)  # 检测间隔
    params = models.CharField(max_length=1024, default='', null=True, blank=True)  # 检测参数
    status_description = models.CharField(max_length=2048, default='', null=True, blank=True)    # 状态说明


class ExamTask(models.Model):
    TopicProblem = constant.TopicProblem
    Status = constant.Status

    exam = models.ForeignKey(Mission, on_delete=models.CASCADE)
    task_title = models.CharField(max_length=100)
    task_content = models.CharField(max_length=1024)
    task_type = models.PositiveIntegerField(default=TopicProblem.SINGLE)
    option = models.TextField(null=True, blank=True)
    answer = models.CharField(max_length=100)
    task_index = models.IntegerField(null=True)
    task_score = models.IntegerField(default=0)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()
