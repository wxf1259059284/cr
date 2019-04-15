from rest_framework import serializers

from base_traffic.models import IntelligentTraffic
from base_traffic.cms.error import TrafficError


def suffix_rules(value):
    if value not in [IntelligentTraffic.Suffix.PY, IntelligentTraffic.Suffix.SH]:
        raise serializers.ValidationError(TrafficError.FIELD_INVALID)


def pcap_file_rules(value):
    if not value.name.endswith('.pcap'):
        raise serializers.ValidationError(TrafficError.PLEASE_UPLOAD_PCAP)


def character_validation(value):
    forbidden_list = ['<script>', '<script>alert', '@', '$']
    for char in forbidden_list:
        if char in value:
            raise serializers.ValidationError(TrafficError.INVALID_CHARACTER)
