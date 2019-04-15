# -*- coding: utf-8 -*-
import commands
import json
import random

import time
from django.conf import settings

from base.utils.models.common import get_obj
from cr_scene import app_settings
from cr_scene.models import CrEvent
from cr_scene.web.serializers import CrEventDetailSerializers
from sisdk import CpVisCr
from base.utils.thread import async_exe


def check_vis_is_run():
    # 检查态势服务是否可用
    vis_host = settings.VIS_HOST
    status, output = commands.getstatusoutput('curl {} -L'.format(vis_host))
    if '</html>' not in output:
        return False
    return True


class VisApi(object):
    DEFAULT_ROOT_ENTITY = 'Internet'
    COLORS = ['#CC3300', '#FFFF66', '#00FF00', '#0099FF', '#000000', '#FFFFFF']

    def __init__(self, cr_event_id_or_obj):
        self.cr_event_obj = get_obj(cr_event_id_or_obj, CrEvent)
        self.vis_cr = CpVisCr(id=self.cr_event_obj.id, title=self.cr_event_obj.name, redis_conf=app_settings.REDIS_CONF)
        self.root_entity = ''

    def get_root_entity(self):
        return self.root_entity and self.root_entity or self.DEFAULT_ROOT_ENTITY

    def _get_json_config(self, request):
        """获取实例的基础拓扑,其中有一个场景或者多个场景"""
        cr_event_data = CrEventDetailSerializers(self.cr_event_obj, context={'request': request}).data
        topo_data_list = []
        for cr_event_scene in cr_event_data["cr_event_scenes"]:
            if cr_event_scene["cr_scene"] and cr_event_scene["cr_scene"]["scene_config"] and \
                    cr_event_scene["cr_scene"]["scene_config"]["json_config"]:
                json_config = cr_event_scene["cr_scene"]["scene_config"]["json_config"]
                # todo  每个场景的根节点
                topo_data_list.append((json_config, 'Internet'))
        return topo_data_list

    def _get_root_entiry(self):
        pass

    def topo_generate(self, request):
        """拓扑生成到态势上"""
        json_data = self._get_json_config(request)
        # json_data = [(json_config, 'Internet'), (json_config1, 'Internet')]
        if len(json_data) == 1:
            self.vis_cr.cr_topology_init_scene(json_data[0][0], json_data[0][1])
        else:
            self.vis_cr.cr_topology_init_multi_scene(json_data, root_name=self.get_root_entity())

    def sync_time(self):
        self.vis_cr.cr_sysctrl_sync_timing()

    def set_logo(self):
        self.vis_cr.cr_ui_set_logo(app_settings.DEFAULT_TOPO_LOGO)

    def set_log_message(self, messages):
        self.vis_cr.cr_ui_log_message(message_text=messages)

    def loading(self, request):
        self.topo_generate(request)
        self.sync_time()
        self.set_logo()
        self.set_log_message("-".join([self.cr_event_obj.name, u"拓扑载入完成！"]))
        # self.vis_cr.cr_ui_chart_panel_close('BAR1')
        # self.vis_cr.cr_ui_chart_panel_close('PIE1')
        # self.vis_cr.cr_ui_chart_panel_close('RADAR1')
        # self.vis_cr.cr_ui_chart_panel_close('LINE1')

    def test_simulated_attack(self, request):
        # 测试模拟攻击 , 模拟攻击时长１小时
        topo_data_list = self._get_json_config(request)
        hosts_servers_list = []  # 个个队伍中的所有主机
        for json_data in topo_data_list:
            network_data = json.loads(json_data[0])
            host_names = {server['id']: server['name'] for server in network_data['servers']}
            hosts_servers_list.append(host_names)
        count = 0
        while count < 60 * 60:
            for hosts_server in hosts_servers_list:
                host1 = random.choice(hosts_server.keys())
                host2 = random.choice(hosts_server.keys())
                suc = random.choice([True, False])
                self.vis_cr.cr_topology_act_attack(host1, host2, suc, True, "", "")
                self.vis_cr.cr_ui_log_message(
                    u"发生攻击: %s-->%s" % (hosts_server.get(host1, 'server-1'), hosts_server.get(host2, 'server-2')))
            time.sleep(5)
            count += 5

    def exe_sync_attack(self, request):
        async_exe(self.test_simulated_attack, args=(request,), delay=10)
