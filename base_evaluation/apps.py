# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.utils.app import AppConfig as BaseAppConfig


class AppConfig(BaseAppConfig):
    name = 'base_evaluation'

    def ready(self):
        from django.db.models.signals import post_save
        from base_evaluation.signals import record_synchronization
        from cr_scene.models import MissionAgentUpload

        post_save.connect(record_synchronization, sender=MissionAgentUpload)
