# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.conf import settings

ORG_DEPTH = 4

# 默认用户头像
DEFAULT_USER_LOGO_DIR = 'user_logo/default_user_logo/'


def load_related(app_settings):
    app_settings.FULL_DEFAULT_USER_LOGO_DIR = os.path.join(settings.MEDIA_ROOT, app_settings.DEFAULT_USER_LOGO_DIR)
