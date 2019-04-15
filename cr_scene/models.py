# -*- coding: utf-8 -*-
import uuid

from django.db import models
from django.utils import timezone

from base.utils.enum import Enum
from base.utils.models.manager import MManager
from base_auth.models import User, Owner
from base_mission.models import Mission
from base_scene.models import SceneConfig, Scene
from traffic_event.models import TrafficEvent


def tool_hash():
    return "{}.event".format(uuid.uuid4())


# cr-scene --> 结合SceneConfig, mission, traffic_event
class CrScene(models.Model):
    name = models.CharField(max_length=225, unique=True)
    scene_config = models.OneToOneField(SceneConfig, on_delete=models.PROTECT)
    scene = models.ForeignKey(Scene, on_delete=models.SET_NULL, null=True, default=None)
    roles = models.TextField(default='[]')
    missions = models.ManyToManyField(Mission)
    traffic_events = models.ManyToManyField(TrafficEvent)
    cr_scene_config = models.TextField(default='{}')
    create_time = models.DateTimeField(default=timezone.now)

    # 实例状态
    Status = Enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)

    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()

    def __unicode__(self):
        return '%s' % self.name


# 靶场实例
class CrEvent(Owner):
    name = models.CharField(max_length=225, unique=True)
    logo = models.ImageField(upload_to='event_logo', default='event_logo/default_event_logo/img1.png')
    description = models.TextField(default='')
    hash = models.CharField(max_length=100, null=True, default=tool_hash)
    cr_scenes = models.ManyToManyField(CrScene, through='CrEventScene')
    # 实例进程
    Process = Enum(
        INPROGRESS=0,
        COMING=1,
        OVER=2,
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    # 实例状态
    Status = Enum(
        DELETE=0,
        NORMAL=1,
        PAUSE=2,
        INPROGRESS=3,
        OVER=4,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)  # 实例正常

    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()

    def __unicode__(self):
        return '%s' % self.name


class CrEventScene(models.Model):
    cr_event = models.ForeignKey(CrEvent, on_delete=models.CASCADE, related_name='creventscene_crevent')
    cr_scene = models.ForeignKey(CrScene, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default='')
    roles = models.TextField(default='[]')
    cr_scene_instance = models.ForeignKey(Scene, on_delete=models.SET_NULL, null=True, default=None)
    extra = models.TextField(default='')


# 实例 任务/流量
class CrSceneEventTask(models.Model):
    cr_event = models.ForeignKey(CrEvent, on_delete=models.PROTECT)
    # 任务hash, 事件hash, hash后缀.mission, .tarffic
    hash = models.CharField(max_length=500)
    score = models.FloatField(default=0)

    # 类型, 考试， CTF, ManualCheck, SystemCheck, AgentCheck, 事件
    Type = Enum(
        EXAM=0,
        CTF=1,
        MANUAL=2,
        SYSTEM=3,
        AGENT=4,
        TRAFFIC=5
    )
    type = models.PositiveIntegerField()

    # 任务/事件 状态
    Status = Enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)


# 用户提交日志
class CrSceneEventUserSubmitLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    cr_event = models.ForeignKey(CrEvent, on_delete=models.PROTECT)
    mission = models.ForeignKey(Mission, on_delete=models.PROTECT)
    answer = models.TextField(null=True, blank=True)
    score = models.FloatField(default=0)
    is_solved = models.BooleanField(default=False)
    is_new = models.BooleanField(default=True)
    time = models.DateTimeField(default=timezone.now)
    submit_ip = models.CharField(max_length=30, null=True)

    # class Meta:
    #     unique_together = ('user', 'cr_event')


# 用户提交
class CrSceneEventUserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='event_answer_user', null=True, blank=True)
    cr_event = models.ForeignKey(CrEvent, on_delete=models.PROTECT)
    mission = models.ForeignKey(Mission, on_delete=models.PROTECT)
    answer = models.TextField(null=True, blank=True)
    score = models.DecimalField(default=0, max_digits=12, decimal_places=4)
    last_edit_time = models.DateTimeField(default=timezone.now)
    last_edit_user = models.ForeignKey(User, null=True, on_delete=models.PROTECT,
                                       related_name='event_answer_last_edit_user', blank=True)

    class Meta:
        unique_together = ('user', 'cr_event', 'mission')


# 前台check的日志
class CrSceneMissionCheckLog(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    check_time = models.DateTimeField(auto_now=True)
    cr_event = models.ForeignKey(CrEvent, on_delete=models.PROTECT, null=True, blank=True)
    score = models.FloatField(default=0)
    is_solved = models.BooleanField(default=False)
    target_ip = models.CharField(max_length=30, null=True)
    script = models.CharField(max_length=1024, null=True)


# 后台测试check日志表
class CmsTestCheckLog(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    cr_scene = models.ForeignKey(CrScene, on_delete=models.PROTECT, null=True, blank=True)
    check_time = models.DateTimeField(auto_now=True)
    score = models.FloatField(default=0)
    is_solved = models.BooleanField(default=False)
    target_ip = models.CharField(max_length=30, null=True)
    script = models.CharField(max_length=1024, null=True)


class CmsAgentTestCheckLog(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.PROTECT)
    cr_scene = models.ForeignKey(CrScene, on_delete=models.PROTECT, null=True, blank=True)
    result = models.TextField(null=True, blank=True)
    is_solved = models.BooleanField(default=False)
    create_time = models.DateTimeField(default=timezone.now)


# 前台Agent上报日志
class CrSceneAgentMissionLog(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.PROTECT)
    cr_event = models.ForeignKey(CrEvent, on_delete=models.PROTECT, null=True, blank=True)
    result = models.TextField(null=True, blank=True)
    is_solved = models.BooleanField(default=False)
    create_time = models.DateTimeField(default=timezone.now)


# 后台测试check结果记录表
class CmsTestCheckRecord(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    cr_scene = models.ForeignKey(CrScene, on_delete=models.PROTECT, null=True, blank=True)
    submit_time = models.DateTimeField(auto_now=True)
    score = models.FloatField(default=0)
    target_ip = models.CharField(max_length=30, null=True)
    script = models.CharField(max_length=1024, null=True)


class BaseNotice(models.Model):
    notice = models.CharField(max_length=1024)
    is_topped = models.BooleanField(default=False)
    create_time = models.DateTimeField(default=timezone.now)
    last_edit_time = models.DateTimeField(default=timezone.now)

    # 通知状态
    Status = Enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)

    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()

    class Meta:
        abstract = True


class EventNotice(BaseNotice):
    cr_event = models.ForeignKey(CrEvent, on_delete=models.PROTECT)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='event_notice_create_user')
    last_edit_user = models.ForeignKey(User, null=True, on_delete=models.PROTECT,
                                       related_name='event_notice_last_edit_user')


class MissionAgentUpload(models.Model):
    cr_event = models.ForeignKey(CrEvent, on_delete=models.PROTECT)
    result = models.TextField(null=True)
    machine_id = models.CharField(max_length=10240, null=True)
    create_time = models.DateTimeField(default=timezone.now)


class MissionPeriod(models.Model):
    cr_scene = models.ForeignKey(CrScene, on_delete=models.CASCADE)
    period_name = models.CharField(max_length=100)
    period_index = models.PositiveIntegerField()

    Status = Enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)
    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()


# 记录用户占用标靶的信息
class CrEventUserStandardDevice(Owner):
    cr_event_scene = models.ForeignKey(CrEventScene, on_delete=models.PROTECT)
    standard_device = models.CharField(max_length=100, null=True)

    # 某次启动的scene_id
    scene_id = models.PositiveIntegerField()

    Status = Enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)
    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()

    class Meta:
        unique_together = ('scene_id', 'standard_device')
