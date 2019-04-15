# -*- coding: utf-8 -*-
import json
import logging

from django.core.cache import cache
from django.db import transaction

from base.models import Executor
from base.utils.functional import cached_property
from base.utils.models.common import get_obj
from base.utils.text import md5

from base_proxy import app_settings as proxy_settings
from base_cloud.utils import memcache_lock, MemcacheLockException

from base_scene.models import SceneConfig, SceneNet, SceneGateway, SceneTerminal

from .error import error
from .exceptions import SceneException
from .util.config import ConfigUtil
from .util.scene import SceneUtil
from .scene_config import SceneConfigHandler


logger = logging.getLogger(__name__)


class BaseHandler(object):

    def __init__(self, user, **kwargs):
        self.user = user
        self.proxy = kwargs.get('proxy', False) and proxy_settings.SWITCH
        self.remote = kwargs.get('remote', True)
        self.scene = kwargs.get('scene', None)

    def __call__(self, scene=None):
        self.scene = scene

        if hasattr(self, 'reset_cached_propertys'):
            self.reset_cached_propertys()

        return self

    @cached_property
    def scene_util(self):
        return SceneUtil(self.scene)(self.user, self.remote, self.proxy)

    def get_node_obj(self, model, node_obj=None, sub_id=None):
        if node_obj:
            return get_obj(node_obj, model)

        if sub_id:
            return model.objects.get(scene=self.scene, sub_id=sub_id)

        raise SceneException('get_node_obj args error')

    def _sync_scene(self, model, node_obj=None, sub_id=None):
        node_obj = self.get_node_obj(model, node_obj=node_obj, sub_id=sub_id)
        if not self.scene:
            self.scene = node_obj.scene
        return node_obj

    def get_net_util(self, scene_net=None, sub_id=None):
        scene_net = self._sync_scene(SceneNet, node_obj=scene_net, sub_id=sub_id)
        return self.scene_util.get_net_util(scene_net)

    def get_gateway_util(self, scene_gateway=None, sub_id=None):
        scene_gateway = self._sync_scene(SceneGateway, node_obj=scene_gateway, sub_id=sub_id)
        return self.scene_util.get_gateway_util(scene_gateway)

    def get_terminal_util(self, scene_terminal=None, sub_id=None):
        scene_terminal = self._sync_scene(SceneTerminal, node_obj=scene_terminal, sub_id=sub_id)
        return self.scene_util.get_terminal_util(scene_terminal)


class GetMixin(object):

    def get(self, complete=True, fields=None):
        return self.scene_util.get(complete, fields=fields)

    def get_all_remote_info(self):
        return self.scene_util.get_all_remote_info()

    def get_console_url(self, scene_terminal=None, terminal_sub_id=None):
        terminal_util = self.get_terminal_util(scene_terminal=scene_terminal, sub_id=terminal_sub_id)
        return terminal_util.get_console_url()

    def get_terminal_net_config(self, net_sub_id, scene_terminal=None, terminal_sub_id=None):
        terminal_util = self.get_terminal_util(scene_terminal=scene_terminal, sub_id=terminal_sub_id)
        return terminal_util.get_net_config(net_sub_id)


class CreateMixin(object):

    # 创建唯一标识
    def get_create_key(self, scene_config):
        create_key = md5('{}:{}'.format(
            self.user.id,
            scene_config.id if scene_config.id else md5(scene_config.json_config),
        ))
        return create_key

    def create(self, scene_config, hang_info=None, name_prefix='', float_ips=None, pre_fips=None, status_updated=None,
               prepare=False, super_viewer=False):
        if not isinstance(scene_config, SceneConfig):
            json_config = scene_config.get('json_config')
            SceneConfigHandler.check_config(json_config)
            scene_config = SceneConfig(
                type=scene_config.get('type', SceneConfig.Type.BASE),
                file=scene_config.get('file'),
                json_config=json.dumps(json_config),
                name=json_config['scene']['name']
            )

        config_util = ConfigUtil(self.user, scene_config, hang_info=hang_info, super_viewer=super_viewer)

        try:
            with memcache_lock(cache, self.get_create_key(scene_config), 1, 10):
                with transaction.atomic():
                    self.scene = config_util.create_scene_structure(
                        name_prefix=name_prefix,
                        status_updated=Executor.add_executor(status_updated) if status_updated else None,
                    )
        except MemcacheLockException:
            raise SceneException(error.DUPLICATE_SUBMIT)

        self.scene_util.prepare_create(
            float_ips=float_ips,
            pre_fips=pre_fips,
        )
        self.scene_util.create_resource(prepare=prepare)

        return self.scene

    def create_prepared_terminal(self, scene_terminal=None, terminal_sub_id=None):
        scene_terminal = self._sync_scene(SceneTerminal, node_obj=scene_terminal, sub_id=terminal_sub_id)
        return self.scene_util.create_prepared_terminal(scene_terminal)


class ControlMixin(object):

    def pause(self, sync=False):
        return self.scene_util.pause(sync)

    def recover(self, sync=False):
        return self.scene_util.recover(sync)

    def recreate_terminal(self, scene_terminal=None, terminal_sub_id=None):
        scene_terminal = self._sync_scene(SceneTerminal, node_obj=scene_terminal, sub_id=terminal_sub_id)
        return self.scene_util.recreate_terminal(scene_terminal)

    def restart_terminal(self, scene_terminal=None, terminal_sub_id=None):
        terminal_util = self.get_terminal_util(scene_terminal=scene_terminal, sub_id=terminal_sub_id)
        return terminal_util.restart()


class DeleteMixin(object):

    def delete(self, shutdown=False, sync=False):
        return self.scene_util.delete(shutdown, sync)


# 环境处理, 创建销毁环境
class SceneHandler(GetMixin, CreateMixin, ControlMixin, DeleteMixin, BaseHandler):
    pass
