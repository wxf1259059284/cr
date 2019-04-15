from django.conf.urls import url
from . import api as cms_api

viewsets = [
    cms_api.TrafficEventViewSet,
]

apiurlpatterns = [
    url(r'^manual_traffic/', cms_api.manual_traffic, name='manual_traffic'),
]
