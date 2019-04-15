# -*- coding: utf-8 -*-
import datetime
from rest_framework import serializers


class DashSceneSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        create_time = datetime.datetime.strftime(instance.create_time, "%Y-%m-%d %H:%M:%S")
        return {
            'scene_name': instance.name,
            'user': instance.user.rep_name,
            'create_time': create_time
        }

    pass
