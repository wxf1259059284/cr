# -*- coding: utf-8 -*-
from base_auth import models as auth_models
from base_auth.cms import serializers as cms_serializers


class OrganizationSerializer(cms_serializers.OrganizationSerializer):

    class Meta:
        model = auth_models.Organization
        fields = ('id', 'name', 'parent', 'parent_data')


class UserSerializer(cms_serializers.UserSerializer):

    class Meta:
        model = auth_models.User
        fields = ('id', 'logo', 'profile', 'organization', 'last_login_ip', 'status',
                  'groups', 'rep_name', 'group', 'organization_data', 'is_admin')
        read_only_fields = ('last_login_ip',)
