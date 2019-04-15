# -*- coding: utf-8 -*-
import time
from django.utils import timezone
from random import randint, choice
from django.core.management import BaseCommand

from cr_scene.models import MissionAgentUpload
from cr_scene.web.serializers import AgentSerializer


class Command(BaseCommand):
    def handle(self, *args, **options):
        while True:
            time.sleep(randint(5, 10))

            records = [
                'IP 为 192.168.100.{} 的机器网络无法连接'.format(randint(100, 200)),
                'IP 为 192.168.100.{} 的机器 CPU 当前使用率{}'.format(randint(50, 100), randint(80, 99)),
                'IP 为 192.168.100.{} 的机器当前磁盘剩余容量不足{}G'.format(randint(50, 100), randint(5, 10)),
                'IP 为 192.168.100.{} 的机器 MySQL 服务异常'.format(randint(100, 200)),
                'IP 为 192.168.100.{} 的机器遭遇 DDOS 攻击'.format(randint(100, 200)),
                'IP 为 192.168.100.{} 的机器tmp目录被写入{}个文件'.format(randint(100, 200), randint(1, 5)),
                'IP 为 192.168.100.{} 的机器被上传木马'.format(randint(100, 200)),
            ]

            latest_record = MissionAgentUpload.objects.last()
            data = AgentSerializer(latest_record).data
            data['result'] = choice(records)
            data['create_time'] = timezone.now()

            check_report = AgentSerializer(data=data)
            check_report.is_valid(raise_exception=True)
            check_report.save()
