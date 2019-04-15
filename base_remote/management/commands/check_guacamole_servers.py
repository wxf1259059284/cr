# -*- coding: utf-8 -*-
import logging

from django.core.management import BaseCommand

from base.utils.ssh import ssh

from base_remote import app_settings


logger = logging.getLogger(__name__)


# 检查创建池
class Command(BaseCommand):
    def handle(self, *args, **options):
        check()


def check():
    check_command = '''
if [ ! -d "{guacdrive_dir}" ]; then
  mkdir -p {guacdrive_dir}
fi

if [ ! -d "{recording_dir}" ]; then
  mkdir -p {recording_dir}
fi
    '''.format(
        guacdrive_dir=app_settings.GUACDRIVE_PATH,
        recording_dir=app_settings.RECORDING_SOURCE_PATH,
    )

    for server in app_settings.GUACAMOLE_SERVERS:
        try:
            sc = ssh(server['host_ip'], 22, server['ssh_username'], server['ssh_password'])
            sc.exe(check_command)
        except Exception as e:
            logger.error('check guacamole server fail: %s', e)
