from rest_framework import serializers
from rest_framework.serializers import Serializer
from rest_framework.validators import UniqueValidator

from base.utils.rest.serializers import ModelSerializer
from base_traffic.cms.validate_rules import character_validation

from base_traffic.models import BackgroundTraffic, IntelligentTraffic, Traffic, TrafficCategory
from base_scene.cms.serializers import StandardDeviceSerializer
import validate_rules as traffic_rules


class BaseCategorySerializer(Serializer):
    category_name = serializers.SerializerMethodField()
    category_i18n_name = serializers.SerializerMethodField()

    def get_category_name(self, obj):
        try:
            language = self.context.get("request").LANGUAGE_CODE
            if language != "zh-hans":
                if isinstance(obj, TrafficCategory):
                    return obj.en_name
                else:
                    if obj.category is None:
                        return None
                    return obj.category.en_name
        except Exception:
            pass

        if isinstance(obj, TrafficCategory):
            return obj.cn_name
        else:
            if obj.category is None:
                return None
            return obj.category.cn_name

    def get_category_i18n_name(self, obj):
        if isinstance(obj, TrafficCategory):
            return None
        else:
            if obj.category is None:
                return None
            return TrafficCategorySerializer(obj.category).data


class BaseRepNameSerializer(Serializer):
    rep_name = serializers.SerializerMethodField()

    def get_rep_name(self, obj):
        if obj.create_user:
            return obj.create_user.rep_name
        else:
            return None


class TrafficCategorySerializer(BaseCategorySerializer, ModelSerializer):
    class Meta:
        model = TrafficCategory
        fields = '__all__'
        extra_kwargs = {
            'en_name': {'min_length': 2,
                        'max_length': 20,
                        'validators': [UniqueValidator(queryset=TrafficCategory.objects.all()), character_validation]},
            'cn_name': {'min_length': 2,
                        'max_length': 20,
                        'validators': [UniqueValidator(queryset=TrafficCategory.objects.all()), character_validation]},
        }


class TrafficSerializer(BaseRepNameSerializer, BaseCategorySerializer, ModelSerializer):
    title = serializers.CharField(max_length=20, min_length=2,
                                  validators=[UniqueValidator(queryset=Traffic.objects.all())])
    introduction = serializers.CharField(max_length=1000, min_length=2, default=None)
    public = serializers.BooleanField(default=True)

    class Meta:
        model = Traffic
        fields = ('id', 'title', 'introduction', 'type', 'public',
                  'create_time', 'rep_name', 'category', 'category_name')


class BackgroundTrafficSerializer(TrafficSerializer):
    file_name = serializers.CharField(max_length=20, min_length=2, required=True)
    loop = serializers.FloatField(min_value=0, max_value=10)
    mbps = serializers.FloatField(min_value=0, max_value=10)
    multiplier = serializers.FloatField(min_value=0, max_value=10)
    # pcap_file = serializers.FileField(validators=[traffic_rules.pcap_file_rules])

    class Meta:
        model = BackgroundTraffic
        fields = ('pcap_file', 'loop', 'mbps', 'multiplier', 'file_name', 'trm')


class IntelligentTrafficSerializer(TrafficSerializer):
    suffix = serializers.IntegerField(validators=[traffic_rules.suffix_rules])

    class Meta:
        model = IntelligentTraffic
        fields = ('suffix', 'file_name', 'code', 'tgm')


class BackgroundDataSerializer(BaseRepNameSerializer, BaseCategorySerializer, ModelSerializer):
    pcap_file = serializers.FileField(source='background_traffic.pcap_file')
    file_name = serializers.CharField(source='background_traffic.file_name')
    loop = serializers.CharField(source='background_traffic.loop')
    mbps = serializers.CharField(source='background_traffic.mbps')
    multiplier = serializers.CharField(source='background_traffic.multiplier')
    trm = serializers.SerializerMethodField()

    def get_trm(self, obj):
        return StandardDeviceSerializer(obj.background_traffic.trm).data

    class Meta:
        model = Traffic
        fields = "__all__"


class IntelligentDataSerializer(BaseRepNameSerializer, BaseCategorySerializer, ModelSerializer):
    code = serializers.CharField(source='intelligent_traffic.code')
    file_name = serializers.CharField(source='intelligent_traffic.file_name')
    suffix = serializers.IntegerField(source='intelligent_traffic.suffix')
    tgm = serializers.SerializerMethodField()

    def get_tgm(self, obj):
        return StandardDeviceSerializer(obj.intelligent_traffic.tgm).data

    class Meta:
        model = Traffic
        fields = "__all__"
