# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from base.utils.error import Error
from base.utils.text import trans as _


error = Error(
    # config
    NO_CONFIG=_('无场景配置'),
    DUMPLICATE_NETWORK_ID=_('重复的网络ID: {id}'),
    DUMPLICATE_GATEWAY_ID=_('重复的网关ID: {id}'),
    INVALID_GATEWAY_NETS=_('网关[{id}]连接了无效的网络: {nets}'),
    DUMPLICATE_SERVER_ID=_('重复的终端ID: {id}'),
    CHECKER_SERVER_NOT_EXIST=_('无效的检查终端: {id}'),
    ATTACKER_SERVER_NOT_EXIST=_('无效的攻击终端: {id}'),
    INVALID_SERVER_NETS=_('终端[{id}]连接了无效的网络: {nets}'),
    SERVER_CANT_ACCESS_EXTERNAL_NET=_('终端[{id}]无法连接外网'),

    # scene
    PARSE_SERVER_SCRIPT_VAL_ERROR=_('终端[{id}]解析脚本参数\'{val}\'错误'),
    NVM_NO_CONSOLE=_('非虚拟机终端暂无控制台'),
    LOCAL_CONTAINER_NOT_SUPPORT_IMAGE=_('本地容器不支持保存镜像'),

    NO_ENOUGH_EXTERNAL_NET_PORT=_('外网没有足够的端口'),
    NO_ENOUGH_FLOAT_IP=_('没有足够的外网ip'),
    NO_ENOUGH_IP=_('没有足够的ip'),

    EXIST_STATIC_ROUTE=_('静态路由已存在'),
    ROUTER_NOT_PREPARED=_('路由未准备好'),
    STATIC_ROUTE_NOT_EXIST=_('静态路由不存在'),
    INVALID_STATIC_ROUTE=_('无效的静态路由'),
    EXIST_FIREWALL_RULE=_('防火墙规则已存在'),
    FIREWALL_NOT_PREPARED=_('防火墙未准备好'),
    INVALID_FIREWALL_RULE=_('无效的防火墙规则'),
    INVALID_TUNNEL=_('无效的链路'),

    # device
    DEVICE_NO_SCENE=_('标靶没有机器'),
)
