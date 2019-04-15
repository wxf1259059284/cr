from __future__ import unicode_literals

import logging
import socket

from base.utils.app import load_app_settings
from base_proxy import nginx
from base_proxy import app_settings as proxy_app_settings


app_settings = load_app_settings(__package__)


logger = logging.getLogger(__name__)


def async_init():
    if proxy_app_settings.SWITCH:
        ip = socket.gethostbyname('controller')
        if ip:
            proxy_port = nginx.get_proxy(ip, app_settings.CONSOLE_PORT)
            if not proxy_port or (proxy_port != app_settings.CONSOLE_PROXY_PORT):
                nginx.add_proxy(ip, app_settings.CONSOLE_PORT,
                                proxy_port=app_settings.CONSOLE_PROXY_PORT, timeout=3600)
                nginx.restart_nginx()
