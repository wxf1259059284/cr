# -*- coding: utf-8 -*-
from . import api as cms_api
from django.conf.urls import url
viewsets = (
    cms_api.MissionViewSet,
)


apiurlpatterns = [
    url(r'^control_status/', cms_api.control_mission_status, name='control_status'),
    url(r'^get_params/', cms_api.get_params, name='get_params'),
    url(r'^update_mission_params/', cms_api.update_mission_params, name='update_mission_params')
]
