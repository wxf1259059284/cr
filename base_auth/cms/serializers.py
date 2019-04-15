# -*- coding: utf-8 -*-
import os

import six
from django.contrib.auth.hashers import make_password

from rest_framework import serializers, exceptions
from rest_framework.validators import UniqueValidator

from base.utils.rest.serializers import ModelSerializer

from base_auth import models as auth_models
from base_auth import app_settings
from base_auth.cms.validate_rules import name_rules, username_rules
from base_auth.models import User


class OrganizationSerializer(ModelSerializer):

    parent_data = serializers.SerializerMethodField()

    def get_parent_data(self, obj):
        if obj.parent:
            return OrganizationSerializer(obj.parent).data
        else:
            return None

    class Meta:
        model = auth_models.Organization
        fields = ('id', 'name', 'parent', 'parent_data')


class UserSerializer(ModelSerializer):
    username = serializers.CharField(min_length=5, validators=[UniqueValidator(queryset=User.objects.all()),
                                                               username_rules])
    name = serializers.CharField(validators=[name_rules])
    rep_name = serializers.SerializerMethodField()
    group = serializers.SerializerMethodField()
    organization_data = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    def get_rep_name(self, obj):
        return obj.rep_name

    def get_group(self, obj):
        return obj.group

    def get_organization_data(self, obj):
        if obj.organization:
            return OrganizationSerializer(obj.organization).data
        else:
            return None

    def get_avatar(self, obj):
        if obj.logo:
            return obj.logo.url

    def update(self, instance, validated_data):
        request = self.context['request']
        if '_clear_groups' in request.data:
            validated_data['groups'] = []

        return super(UserSerializer, self).update(instance, validated_data)

    def to_internal_value(self, data):
        if 'groups' in data:
            if not data.get('groups'):
                data._mutable = True
                data.pop('groups')
                data['_clear_groups'] = True
                data._mutable = False

        password = data.get('password', None)

        if password and len(password) < 6:
            raise exceptions.ValidationError({"password": "password length is than less 6"})

        if not self.instance and not password:
            raise exceptions.ValidationError({"password": 'password invalid'})

        logo = data.get('logo')
        default_logo = None
        if logo and isinstance(logo, (six.string_types, six.text_type)):
            default_logo_path = os.path.join(app_settings.FULL_DEFAULT_USER_LOGO_DIR, logo)
            if os.path.exists(default_logo_path):
                data._mutable = True
                default_logo = logo
                data.pop('logo')
                data._mutable = False
        ret = super(UserSerializer, self).to_internal_value(data)
        if default_logo:
            ret['logo'] = os.path.join(app_settings.DEFAULT_USER_LOGO_DIR, default_logo)

        if password:
            ret['password'] = make_password(password)

        return ret

    class Meta:
        model = auth_models.User
        fields = ('id', 'username', 'logo', 'name', 'profile', 'organization', 'last_login_ip',
                  'status', 'groups', 'rep_name', 'group', 'organization_data', 'avatar', 'is_admin')
        read_only_fields = ('last_login_ip',)


class OwnerSerializer(ModelSerializer):
    username = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.rep_name
