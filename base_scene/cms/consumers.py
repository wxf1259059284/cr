
from base.utils.models.common import get_obj
from base.utils.enum import Enum
from base_auth.utils.common import get_user
from base_auth.cms.consumers import UserWebsocket

from base_scene.common.scene import SceneHandler
from base_scene.models import StandardDevice, Scene, SceneNet, SceneTerminal
from . import serializers as mserializers


class StandardDeviceWebsocket(UserWebsocket):

    Event = Enum(
        SCENE_STATUS_UPDATE=1,
        IMAGE_STATUS_UPDATE=2,
    )

    @classmethod
    def _get_device_data(cls, user, device):
        user = get_user(user)
        device = get_obj(device, StandardDevice)
        data = mserializers.StandardDeviceSerializer(device, context={'user': user}).data
        return data

    @classmethod
    def scene_status_update(cls, user, device):
        data = cls._get_device_data(user, device)
        cls.user_send(user, data, code=cls.Event.SCENE_STATUS_UPDATE)

    @classmethod
    def image_status_update(cls, user, device):
        data = cls._get_device_data(user, device)
        cls.user_send(user, data, code=cls.Event.IMAGE_STATUS_UPDATE)


class SceneWebsocket(UserWebsocket):

    Event = Enum(
        SCENE_STATUS_UPDATE=1,
        SCENE_NET_STATUS_UPDATE=2,
        SCENE_GATEWAY_STATUS_UPDATE=3,
        SCENE_TERMINAL_STATUS_UPDATE=4,
    )

    @classmethod
    def _get_scene_data(cls, user, scene, fields=None):
        user = get_user(user)
        scene = get_obj(scene, Scene)
        handler = SceneHandler(user, scene=scene)
        data = handler.scene_util.get_data(fields=fields)
        return data

    @classmethod
    def _get_scene_net_data(cls, user, scene_net, fields=None):
        user = get_user(user)
        scene_net = get_obj(scene_net, SceneNet)
        handler = SceneHandler(user)
        net_util = handler.get_net_util(scene_net)
        data = net_util.get_data(fields=fields)
        return data

    @classmethod
    def _get_scene_terminal_data(cls, user, scene_terminal, fields=None):
        user = get_user(user)
        scene_terminal = get_obj(scene_terminal, SceneTerminal)
        handler = SceneHandler(user)
        terminal_util = handler.get_terminal_util(scene_terminal)
        data = terminal_util.get_data(fields=fields)
        return data

    @classmethod
    def scene_status_update(cls, user, scene, fields=None):
        data = cls._get_scene_data(user, scene, fields=fields)
        cls.user_send(user, data, code=cls.Event.SCENE_STATUS_UPDATE)

    @classmethod
    def scene_net_status_update(cls, user, scene_net, fields=None):
        data = cls._get_scene_net_data(user, scene_net, fields=fields)
        cls.user_send(user, data, code=cls.Event.SCENE_NET_STATUS_UPDATE)

    @classmethod
    def scene_terminal_status_update(cls, user, scene_terminal, fields=None, data_handler=None):
        data = cls._get_scene_terminal_data(user, scene_terminal, fields=fields)
        if data_handler:
            data_handler(data)
        cls.user_send(user, data, code=cls.Event.SCENE_TERMINAL_STATUS_UPDATE)
