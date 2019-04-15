# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from base.utils.models.manager import MManager
from base_auth.models import User
from base_scene.models import StandardDevice
from .cms import constant


class MonitorCategory(models.Model):
    Status = constant.Status

    cn_name = models.CharField(max_length=100)
    en_name = models.CharField(max_length=100)
    status = models.IntegerField(default=Status.NORMAL)

    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()


class Scripts(models.Model):
    Suffix = constant.Suffix
    Status = constant.Status
    Type = constant.ScriptType

    type = models.PositiveIntegerField(default=Type.REMOTE)
    public = models.BooleanField(default=True)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    title = models.CharField(max_length=1024)
    desc = models.CharField(max_length=1024, null=True, blank=True)
    code = models.TextField()

    category = models.ForeignKey(MonitorCategory, on_delete=models.SET_NULL, null=True)

    checker = models.ForeignKey(StandardDevice, blank=True, null=True)
    # path = models.FileField(upload_to='scene/scripts', null=True, default=None)
    suffix = models.PositiveIntegerField(default=Suffix.PY)
    create_time = models.DateTimeField(auto_now_add=True)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='script_create_user', null=True,
                                    default=None)
    last_edit_user = models.ForeignKey(User, default=None, on_delete=models.SET_NULL, null=True,
                                       related_name='script_last_edit_user')
    last_edit_time = models.DateTimeField(auto_now=True)

    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()
