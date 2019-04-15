from . import api as cms_api

viewsets = [
    cms_api.TrafficViewSet,
    cms_api.BackgroundTrafficViewSet,
    cms_api.IntelligentTrafficViewSet,
    cms_api.TrafficCategoryViewSet
]
