import logging

from django.conf import settings
from base.utils.app import load_app_settings


logger = logging.getLogger(__name__)

app_settings = load_app_settings(__package__)


def sync_init():
    settings.DATABASES['guacamole'] = app_settings.DATABASE
