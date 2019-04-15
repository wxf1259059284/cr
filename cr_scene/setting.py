# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.conf import settings

# True: 其中一个管理员就是该实例下的全部管理员
# False: 各个场景里面的的管理员控制自己的
CHECKER_ONE_AS_ADMIN = True

# 默认实例头像
DEFAULT_EVENT_LOGO_DIR = 'event_logo/default_event_logo/'

# 态势拓扑显示logo
DEFAULT_TOPO_LOGO = 'http://58.213.63.28:9098/static/logos/cpcr.png'

REDIS_CONF = {
    'host': '127.0.0.1',
    'port': 6379,
    'password': settings.REDIS_PASS,
}


def load_related(app_settings):
    app_settings.FULL_DEFAULT_EVENT_LOGO_DIR = os.path.join(settings.MEDIA_ROOT, app_settings.DEFAULT_EVENT_LOGO_DIR)
