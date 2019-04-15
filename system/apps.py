# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.utils.app import AppConfig as BaseAppConfig


class AppConfig(BaseAppConfig):
    name = 'system'

    def ready(self):
        from django.db.models.signals import post_save
        from system.models import UpgradeVersion
        from system.signals import upgrade_cr

        post_save.connect(upgrade_cr, sender=UpgradeVersion)
