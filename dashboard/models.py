# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from django.db import models


class SystemUseStatus(models.Model):
    alert_time = models.DateTimeField(default=datetime.now)
    vcpu = models.CharField(max_length=200, default=None)
    ram = models.CharField(max_length=200, default=None)
    disk = models.CharField(max_length=200, default=None)
