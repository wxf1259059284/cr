# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from base.utils.enum import Enum

Status = Enum(
    FAIL=1,
    SUCCESS=2,
)


class UpgradeVersion(models.Model):
    upgrade_package = models.FileField(upload_to='upgrade')
    info = models.TextField(default='')
    create_time = models.DateTimeField(auto_now_add=True)
    upgrade_status = models.PositiveIntegerField(default=Status.SUCCESS)

    class Meta:
        db_table = 'system_upgrade_info'
