from django.conf.urls import url

from . import api
from . import rest_views


viewsets = (
    api.StandardDeviceViewSet,
    api.StandardDeviceSnapshotViewSet,
    # api.NetworkViewSet,
    # api.InstallerTypeViewSet,
    # api.InstallerViewSet,
)

apiurlpatterns = [
    url(r'^report_server_status/$', rest_views.report_server_status, name='report_server_status'),
]
