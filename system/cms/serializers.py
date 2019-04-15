# -*- coding: utf-8 -*-
from base.utils.rest.serializers import ModelSerializer

from ..models import UpgradeVersion


class UpgradeVersionSerializer(ModelSerializer):
    class Meta:
        model = UpgradeVersion
        fields = '__all__'
