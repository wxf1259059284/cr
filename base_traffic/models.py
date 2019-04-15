# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import uuid

from django.db import models

from base.utils.enum import Enum
from base.utils.models.manager import MManager
from base_auth.models import User
from base_scene.models import StandardDevice


def tool_hash():
    return "{}.traffic".format(uuid.uuid4())


class TrafficCategory(models.Model):
    Status = Enum(
        DELETE=0,
        NORMAL=1,
    )

    cn_name = models.CharField(max_length=64)
    en_name = models.CharField(max_length=64)
    status = models.IntegerField(default=Status.NORMAL)

    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()


class Traffic(models.Model):
    title = models.CharField(max_length=64)
    introduction = models.TextField(null=True, default='', blank=True)
    Type = Enum(
        BACKGROUND=1,
        INTELLIGENT=2,
    )
    type = models.PositiveIntegerField(default=Type.BACKGROUND)
    public = models.BooleanField(default=True)
    is_copy = models.BooleanField(default=False)
    hash = models.CharField(max_length=100, null=True, default=tool_hash)
    category = models.ForeignKey(TrafficCategory, on_delete=models.SET_NULL, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='traffic_create_user', null=True,
                                    default=None)
    last_edit_user = models.ForeignKey(User, default=None, on_delete=models.SET_NULL, null=True,
                                       related_name='traffic_last_edit_user')
    last_edit_time = models.DateTimeField(auto_now=True)
    Status = Enum(
        DELETE=0,
        NORMAL=1
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)
    parent = models.PositiveIntegerField(null=True)
    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()

    def __unicode__(self):
        return '%s' % self.title


class BackgroundTraffic(models.Model):
    traffic = models.OneToOneField(Traffic, primary_key=True, related_name='background_traffic')
    pcap_file = models.FileField(upload_to='traffic/pcap')
    file_name = models.CharField(max_length=100, default=None)
    trm = models.ForeignKey(StandardDevice, related_name='traffic_trm',
                            on_delete=models.SET_NULL, null=True, default=None)
    Loop = Enum(
        LOOP=0,
        ONCE=1
    )
    loop = models.PositiveIntegerField(default=Loop.ONCE)
    mbps = models.PositiveIntegerField(null=True)
    multiplier = models.FloatField()


class IntelligentTraffic(models.Model):
    traffic = models.OneToOneField(Traffic, primary_key=True, related_name='intelligent_traffic')
    Suffix = Enum(
        PY=0,
        SH=1
    )
    code = models.TextField(default=None)
    file_name = models.CharField(max_length=100, blank=True)
    suffix = models.PositiveIntegerField(default=Suffix.PY)
    tgm = models.ForeignKey(StandardDevice, related_name='traffic_tgm',
                            on_delete=models.SET_NULL, null=True, default=None)
