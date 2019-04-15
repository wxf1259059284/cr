from django.conf.urls import url
from . import api
viewsets = (
    api.AgentViewSet,
)


apiurlpatterns = [
    url(r'^get_traffic_event_status/', api.get_traffic_event_status, name='get_traffic_event_status'),
]
