# -*- coding: utf-8 -*-
import json

from django.utils import six
from channels import Group
from channels.generic.websockets import JsonWebsocketConsumer


class Websocket(JsonWebsocketConsumer):

    http_user_and_session = True

    path_name = ''

    @classmethod
    def as_new_route(cls, path):
        if cls.path_name:
            route_path = r'^{path}/{path_name}/$'.format(path=path, path_name=cls.path_name)
        else:
            route_path = r'^{path}/$'.format(path=path)
        return cls.as_route(path=route_path)

    @classmethod
    def group_prefix(cls):
        return '%s-%s' % (cls.__module__, cls.__name__)

    @classmethod
    def get_group_name(cls, name):
        return '%s.%s' % (cls.group_prefix(), name)

    @classmethod
    def get_group(cls, name):
        return Group(cls.get_group_name(name))

    @classmethod
    def group_send(cls, name, content, close=False, code=None):
        if code is not None:
            content = {
                'code': code,
                'data': content,
            }
        JsonWebsocketConsumer.group_send(cls.get_group_name(name), content, close=close)

    def get_connection_groups(self, message, **kwargs):
        return []

    def connect(self, message, **kwargs):
        if not message.user.is_authenticated:
            message.reply_channel.send({"close": True})
            return

        message.reply_channel.send({"accept": True})
        for group in self.get_connection_groups(message, **kwargs):
            self.get_group(group).add(message.reply_channel)

    def receive(self, content, **kwargs):
        message = self.message
        if not message.user.is_authenticated:
            message.reply_channel.send({"close": True})
            return

        self.send(content)

    def disconnect(self, message, **kwargs):
        if not message.user.is_authenticated:
            message.reply_channel.send({"close": True})
            return

        for group in self.get_connection_groups(message, **kwargs):
            self.get_group(group).discard(message.reply_channel)


def send(group, content):
    if not isinstance(content, six.string_types):
        content = json.dumps(content)

    group.send({'text': content})
