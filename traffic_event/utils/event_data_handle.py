from rest_framework import exceptions

from traffic_event.cms.error import error
from traffic_event.cms.constants import EventType
from base_traffic.cms.serializers import BackgroundTrafficSerializer


def save_related_traffic(request, traffic):
    if not traffic.type:
        raise exceptions.ValidationError(error.TRAFFIC_ERROR)

    if traffic.type == EventType.BACKGROUND:
        static_data = {}
        static_data['loop'] = request.data.get('loop') or traffic.background_traffic.loop
        static_data['mbps'] = request.data.get('mbps') or traffic.background_traffic.mbps
        static_data['multiplier'] = request.data.get('multiplier') or traffic.background_traffic.multiplier
        static_serializer = BackgroundTrafficSerializer(traffic.background_traffic, data=static_data, partial=True)
        static_serializer.is_valid(raise_exception=True)
        static_serializer.save()

    if traffic.type == EventType.INTELLIGENT:
        pass
