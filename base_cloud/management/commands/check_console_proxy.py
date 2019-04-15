# -*- coding: utf-8 -*-
import logging
import socket

from django.core.management import BaseCommand

from base_proxy import nginx
from base_proxy import app_settings as proxy_app_settings
from base_cloud import app_settings


logger = logging.getLogger(__name__)


# 检查创建池
class Command(BaseCommand):
    def handle(self, *args, **options):
        check()


def check():
    if proxy_app_settings.SWITCH:
        ip = socket.gethostbyname('controller')
        if ip:
            proxy_port = nginx.get_proxy(ip, app_settings.CONSOLE_PORT)
            if not proxy_port or (proxy_port != app_settings.CONSOLE_PROXY_PORT):
                nginx.add_proxy(ip, app_settings.CONSOLE_PORT,
                                proxy_port=app_settings.CONSOLE_PROXY_PORT, timeout=3600)
                nginx.restart_nginx()
