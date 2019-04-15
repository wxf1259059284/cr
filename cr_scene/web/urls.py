# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import api

viewsets = (
    api.CrSceneViewSet,
    api.CrEventViewSet,
    api.EventNoticeViewSet,
    api.AgentViewSet,
    api.CrEventUserStandardDeviceViewSet,
)

apiurlpatterns = [
    url(r'^show_vis/(?P<pk>\d+)', api.show_vis, name='show_vis'),
]
