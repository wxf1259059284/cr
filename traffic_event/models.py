# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from base.utils.enum import Enum
from base.utils.models.manager import MManager
from base_auth.models import User
from base_traffic.models import Traffic


class TrafficEvent(models.Model):
    title = models.CharField(max_length=64)
    introduction = models.TextField(null=True, default='', blank=True)
    Type = Enum(
        BACKGROUND=1,
        INTELLIGENT=2,
    )
    type = models.PositiveIntegerField(default=Type.BACKGROUND)
    StartUpMode = Enum(
        AUTO=1,
        DELAY=2
    )
    start_up_mode = models.PositiveIntegerField(default=StartUpMode.AUTO)
    delay_time = models.PositiveIntegerField(null=True)
    public = models.BooleanField(default=True)
    traffic = models.ForeignKey(Traffic, related_name='traffic_event')
    target = models.CharField(max_length=128, default=None, blank=True)
    runner = models.CharField(max_length=100, default=None)
    target_net = models.CharField(max_length=100, default=None)
    parameter = models.CharField(max_length=200, default='', blank=True)
    pid = models.CharField(max_length=128, default='')
    create_time = models.DateTimeField(auto_now_add=True)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT,
                                    related_name='event_traffic_create_user', null=True, default=None)
    last_edit_user = models.ForeignKey(User, default=None, on_delete=models.SET_NULL, null=True,
                                       related_name='event_traffic_last_edit_user')
    last_edit_time = models.DateTimeField(auto_now=True)
    Status = Enum(
        DELETE=0,
        NORMAL=1,
        RUNNING=2,
        ERROR=3,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)
    error = models.TextField(max_length=2048, default=None, null=True)
    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()
