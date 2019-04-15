from rest_framework import serializers

from base.utils.rest.serializers import ModelSerializer
from base_traffic.cms.serializers import BackgroundDataSerializer, IntelligentDataSerializer, BaseRepNameSerializer
from traffic_event.models import TrafficEvent


class BaseCategorySerializer(ModelSerializer):
    category = serializers.SerializerMethodField()

    def get_category(self, obj):
        return obj.traffic.category.id if obj.traffic.category else None


class TrafficEventSerializer(BaseRepNameSerializer, ModelSerializer):
    class Meta:
        model = TrafficEvent
        fields = "__all__"


class BackgroundTrafficEventSerializer(BaseCategorySerializer, BaseRepNameSerializer, ModelSerializer):
    traffic = BackgroundDataSerializer()

    class Meta:
        model = TrafficEvent
        fields = "__all__"


class IntelligentTrafficEventSerializer(BaseCategorySerializer, BaseRepNameSerializer, ModelSerializer):
    traffic = IntelligentDataSerializer()

    class Meta:
        model = TrafficEvent
        fields = "__all__"
