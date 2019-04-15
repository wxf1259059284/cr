
from django.contrib.auth import authenticate, login
from django.contrib.sessions.models import Session
from django.utils.decorators import classonlymethod

from rest_framework import exceptions, filters, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from base.utils.rest.mixins import CacheModelMixin, PMixin

from base_auth.models import Organization, User
from base_auth.utils.rest.decorators import org_queryset

from . import serializers as mserializers
from .error import error


class SessionViewSet(PMixin, viewsets.ViewSet):
    queryset = Session.objects.all()
    permission_classes = (AllowAny,)

    @classonlymethod
    def as_csrf_view(cls, actions=None, **initkwargs):
        view = cls.as_view(actions, **initkwargs)
        view.csrf_exempt = False
        return view

    def create(self, request):
        username = self.shift_data.get('username')
        password = self.shift_data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise exceptions.AuthenticationFailed(error.AUTHENTICATION_FAILED)
        login(request, user)
        user_data = mserializers.UserSerializer(user).data
        user_data['token'] = request.META['CSRF_COOKIE']
        user_data['session'] = request.session.session_key
        return Response(user_data, status=status.HTTP_200_OK)


class OrganizationViewSet(CacheModelMixin, PMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = mserializers.OrganizationSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('id',)
    ordering = ('id',)
    unlimit_pagination = True


class UserViewSet(CacheModelMixin, PMixin, viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = mserializers.UserSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('username', 'nickname', 'name')
    ordering_fields = ('id',)
    ordering = ('-id',)

    @org_queryset
    def get_queryset(self):
        queryset = self.queryset

        exclude = self.query_data.getlist('exclude', int)
        if exclude:
            queryset = queryset.exclude(pk__in=exclude)

        organization = self.query_data.get('organization', int)
        if organization is not None:
            queryset = queryset.filter(organization=organization)

        group = self.query_data.getlist('group', User.Group.values())
        if group:
            queryset = queryset.filter(groups=group)

        return queryset
