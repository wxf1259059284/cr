# -*-coding: utf-8 -*-
from channels import Channel

from base.utils.rpc.client import AgentClient
from base_traffic.traffic.delay_traffic import manual_traffic
from base_traffic.utils.traffic import get_terminal_info
from base_traffic.utils.traffic_logger import TrafficLogFactory
from cr_scene.utils.checker_info import get_checker_ip
from traffic_event.models import TrafficEvent


class TrafficEventManager(object):
    start_params = ['runner_ip', 'runner_port', 'target_name', 'target_ip',
                    'target_mac', 'traffic_event_id', 'scene_id']
    stop_params = ['runner_ip', 'runner_port', 'traffic_event', 'scene_id']

    def __init__(self, traffic_event, scene_id):
        self.traffic_event = traffic_event
        self.traffic_event_id = traffic_event.id
        self.scene_id = scene_id
        self.logger = TrafficLogFactory(scene_id, __name__)
        self.runner_ip, self.runner_port = get_checker_ip(scene_id, traffic_event.runner)
        self.target_name, self.target_ip, self.target_mac = get_terminal_info(
            scene_id,
            traffic_event.target,
            traffic_event.target_net
        )

    def check_params(self, params_list):
        if not all([getattr(self, p) for p in params_list]):
            self.logger.error('TrafficEvent[%s]: Get runner&target info error', self.traffic_event.title)
            return False
        return True

    def get_params(self, params_list):
        return {p: getattr(self, p) for p in params_list}

    def start(self, manual=False):
        """
        :param manual: 手动启动
        :return:
        """
        if not self.check_params(self.start_params):
            return None
        data = self.get_params(self.start_params)
        self.logger.info("TrafficEvent[%s]: TrafficMachine(%s)---> %s(%s)",
                         self.traffic_event.title, self.runner_ip, self.target_name, self.target_ip)
        if manual:
            return manual_traffic(data)

        else:
            delayed_message = {
                'channel': 'traffic',
                'content': data,
                'delay': self.traffic_event.delay_time * 1000 * 60
            }
            Channel('asgi.delay').send(delayed_message)
            self.logger.info("Channel send delay task, traffic [%s] minutes later", self.traffic_event.delay_time)

    def stop(self):
        self.check_params(self.stop_params)
        self.traffic_event.status = TrafficEvent.Status.NORMAL

        ac = AgentClient(self.runner_ip, self.runner_port)
        command = "kill -9 %s" % self.traffic_event.pid
        self.traffic_event.save()
        _ret = ac.execute_command(command)
        if _ret['status'] == 'ok' or (
                _ret['status'] == 'error' and _ret['content'].split(":")[0] == "Non zero exit code"):
            self.logger.info("TrafficEvent[%s]: stop success", self.traffic_event.title)
            return {'status': 'ok'}

        else:
            return _ret
