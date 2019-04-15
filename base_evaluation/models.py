# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone

from base.utils.models.manager import MManager
from base_auth.models import User
from cr_scene.models import CrEvent
from .constant import EvaluationStatus, Status


class CheckReport(models.Model):
    cr_event = models.ForeignKey(CrEvent, on_delete=models.PROTECT)
    result = models.TextField(null=True)
    machine_id = models.CharField(max_length=10240, null=True)
    create_time = models.DateTimeField(default=timezone.now)


class EvaluationReport(models.Model):
    report = models.OneToOneField(CheckReport, related_name='check_report')

    evaluation_status = models.PositiveIntegerField(default=EvaluationStatus.WAIT)
    evaluator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.PositiveIntegerField(default=Status.NORMAL)

    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()
