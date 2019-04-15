from base.utils.rest.serializers import ModelSerializer
from base_traffic.cms.serializers import BaseRepNameSerializer
from traffic_event.models import TrafficEvent


class TrafficEventSerializer(BaseRepNameSerializer, ModelSerializer):
    class Meta:
        model = TrafficEvent
        fields = ('id', 'title', 'type', 'traffic', 'target', 'target_net', 'runner', 'status')
