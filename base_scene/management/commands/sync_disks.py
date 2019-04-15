# -*- coding: utf-8 -*-
import logging

from django.core.management import BaseCommand

from base_scene.models import Disk


logger = logging.getLogger(__name__)


# 清除没有被使用的安装文件
class Command(BaseCommand):
    def handle(self, *args, **options):
        for disk in Disk.objects.all():
            disk.sync()
