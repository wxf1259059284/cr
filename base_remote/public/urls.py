# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import rest_views

apiurlpatterns = [
    url(r'^connection/(?P<connection_id>[0-9]+)/info/$', rest_views.connection_info, name='connection_info'),
    url(r'^connection/(?P<connection_id>[0-9]+)/enable_recording/$', rest_views.enable_recording,
        name='enable_recording'),
    url(r'^connection/(?P<connection_id>[0-9]+)/disable_recording/$', rest_views.disable_recording,
        name='disable_recording'),
    url(r'^recording_convert/$', rest_views.recording_convert, name='recording_convert'),
    url(r'^recording_convert/(?P<task_id>[0-9]+)/over/$', rest_views.recording_convert_over,
        name='recording_convert_over'),
    url(r'^login_guacamoles/$', rest_views.login_guacamoles, name='login_guacamoles'),
]
