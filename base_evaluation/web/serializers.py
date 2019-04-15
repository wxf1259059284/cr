# -*- coding: utf-8 -*-
from rest_framework import serializers

from base_auth.cms.serializers import UserSerializer
from base_evaluation import models as evaluation_models


class CheckReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = evaluation_models.CheckReport
        fields = '__all__'


class EvaluationReportSerializer(serializers.ModelSerializer):
    report = CheckReportSerializer()
    evaluator = UserSerializer(fields=('username',))

    class Meta:
        model = evaluation_models.EvaluationReport
        fields = '__all__'
