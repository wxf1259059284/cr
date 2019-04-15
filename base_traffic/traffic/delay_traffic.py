import logging

from base_traffic.traffic.traffic_manager import BackgroundTrafficManager, IntelligentTrafficManager
from traffic_event.models import TrafficEvent
cr_logger = logging.getLogger(__name__)


def delay_traffic(messages):
    data = messages.content

    if not data:
        cr_logger.error("Traffic Event Parameters Error ")

    traffic_event = TrafficEvent.objects.get(pk=data.get('traffic_event_id'))

    if traffic_event.type == TrafficEvent.Type.BACKGROUND:
        traffic = BackgroundTrafficManager(data, traffic_event)
    else:
        traffic = IntelligentTrafficManager(data, traffic_event)

    traffic.run()


def manual_traffic(data):
    traffic_event = TrafficEvent.objects.get(pk=data.get('traffic_event_id'))

    if traffic_event.type == TrafficEvent.Type.BACKGROUND:
        traffic = BackgroundTrafficManager(data, traffic_event)
    else:
        traffic = IntelligentTrafficManager(data, traffic_event)

    return traffic.run()
