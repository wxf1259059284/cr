# -*- coding: utf-8 -*-
from base.utils.rest.mixins import CacheModelMixin, PMixin, DestroyModelMixin
from rest_framework import viewsets, permissions, filters

from ..models import UpgradeVersion
from .serializers import UpgradeVersionSerializer


class UpgradeVersionViewSet(DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = UpgradeVersion.objects.all()
    serializer_class = UpgradeVersionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
