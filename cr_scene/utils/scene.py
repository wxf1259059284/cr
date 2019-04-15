# -*- coding: utf-8 -*-
import functools
import logging

from base_scene.common.util.scene import SceneUtil
from base_scene.common.util.terminal import TerminalUtil
from base_scene.models import Scene, SceneTerminal

LOG = logging.getLogger(__name__)


def logger_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        LOG.debug("Start {}(): args={}, kwargs={}".format(func_name,
                                                          args, kwargs))
        ff = func(*args, **kwargs)
        LOG.debug("End {}()".format(func_name))
        return ff

    return wrapper


def get_scene(scene_id):
    return Scene.objects.filter(id=scene_id).first()


def get_scene_terminal(scene=None, terminal_sub_id=None, terminal_id=None):
    if scene and terminal_sub_id:
        scene_terminal = SceneTerminal.objects.filter(scene=scene, sub_id=terminal_sub_id).first()
    elif terminal_id:
        try:
            scene_terminal = SceneTerminal.objects.get(pk=terminal_id)
        except SceneTerminal.DoesNotExist:
            scene_terminal = None
    else:
        scene_terminal = None

    return scene_terminal


def get_terminal_util(scene=None, terminal_sub_id=None, terminal_id=None, terminal_util=None):
    if terminal_util:
        return terminal_util

    scene_terminal = get_scene_terminal(scene, terminal_sub_id, terminal_id)
    if not scene_terminal:
        return None

    return TerminalUtil(scene_terminal)


# 获取所有远程连接信息
def get_scene_all_remote_info(scene):
    scene_util = SceneUtil(scene)
    return scene_util.get_all_remote_info()


# 获取终端网络配置
def get_terminal_net_config(net_sub_id, scene=None, terminal_sub_id=None, terminal_id=None, terminal_util=None):
    terminal_util = get_terminal_util(scene, terminal_sub_id, terminal_id, terminal_util)
    if not terminal_util:
        return {}

    net_config = terminal_util.get_net_config(net_sub_id)

    return net_config


# 获取终端直连信息
@logger_decorator
def get_terminal_access_infos(scene=None, terminal_sub_id=None, terminal_id=None, terminal_util=None, filters=None):
    terminal_util = get_terminal_util(scene, terminal_sub_id, terminal_id, terminal_util)
    if not terminal_util:
        return []

    access_infos = terminal_util.access_infos
    filters = filters or {}
    protocol = filters.get('protocol') or ''
    port = filters.get('port') or ''
    if protocol or port:
        filter_access_infos = []
        for access_info in access_infos:
            access_key = _protocol_port_key(access_info[0], access_info[2])
            search_key = _protocol_port_key(protocol or access_info[0], port or access_info[2])
            if access_key == search_key:
                filter_access_infos.append(access_info)

            if len(access_info) >= 4:
                source_port_access_key = _protocol_port_key(access_info[0], access_info[3])
                source_port_search_key = _protocol_port_key(protocol or access_info[0], port or access_info[3])
                if source_port_access_key == source_port_search_key:
                    filter_access_infos.append(access_info)

        return filter_access_infos
    else:
        return access_infos


def _protocol_port_key(protocol, port):
    return '{}:{}'.format(protocol, port)
