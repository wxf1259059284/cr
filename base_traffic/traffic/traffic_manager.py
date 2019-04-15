# -*- coding: utf-8 -*-
import json
import os

from base.utils.rpc.client import AgentClient
from base_traffic.traffic.constants import DelayTime
from base_traffic.utils.traffic import get_traffic_script, traffic_params
from base_traffic.utils.traffic_logger import TrafficLogFactory
from traffic_event.models import TrafficEvent


class BaseTraffic(object):
    def __init__(self, data, traffic_event):
        self.data = data
        self.scene_id = data.get('scene_id')
        self.traffic_event = traffic_event
        self.logger = TrafficLogFactory(self.scene_id, __name__)

    def _check(self):
        """
        开始前的检查
        :return: True: 检查成功
        """
        if self.traffic_event.status == TrafficEvent.Status.RUNNING:
            self.logger.info("Traffic[%s]: status is running,no need to repeat", self.traffic_event.title)
            return False

        self.script_path = get_traffic_script(self.traffic_event)
        if not self.script_path:
            self.logger.debug("Traffic[%s] script[%s]: script path is none", self.traffic_event.title)
            return False
        if not os.path.exists(self.script_path):
            self.logger.error("Traffic[%s] script[%s]: does not exist", self.traffic_event.title, self.script_path)
            return False

        return True

    def run(self):
        if not self._check():
            return

        ac = AgentClient(self.data.get('runner_ip'), self.data.get('runner_port'))
        extra_params = traffic_params(self.traffic_event)
        rpc_msg = self._run(self.data, ac, extra_params)
        msg = self.handle_event_status(rpc_msg)
        self._start_check_traffic(ac)
        return msg

    def _run(self, data, agent_client, extra_params):
        raise NotImplementedError('implement in sub class')

    def handle_event_status(self, message):
        if message.get('status') == 'down':
            msg = {'status': 'down', 'msg': 'connection failed'}
            self.traffic_event.status = TrafficEvent.Status.ERROR
            self.traffic_event.error = "TGM Connection Refused!"
            self.logger.error("TrafficEvent[%s]: TGM connection failed!", self.traffic_event.title)
        elif message.get('status') == 'ok':
            msg = self._handle_event_status(message)
        else:
            self.traffic_event.status = TrafficEvent.Status.ERROR
            error_msg = message.get('content') if message.get('content') else 'unknown error'
            self.traffic_event.error = error_msg
            msg = {'status': 'error', 'msg': error_msg}
            self.logger.error("TrafficEvent[%s] running error: %s", self.traffic_event.title, error_msg)
        return msg

    def _handle_event_status(self, message):
        raise NotImplementedError('implement in sub class')

    def _start_check_traffic(self, ac):
        if not self.traffic_event.pid:
            self.logger.info("TrafficEvent[%s]: no pid,reset to default after %ss ",
                             self.traffic_event.title, DelayTime.INTELLIGENT)

        delay_time = DelayTime.BACKGROUND if self.traffic_event.pid else DelayTime.INTELLIGENT
        pid = int(self.traffic_event.pid) if self.traffic_event.pid else None
        parameter = {'pid': pid}
        ac.scheduler_execute_script(
            "base_traffic/utils/check_process.py",
            main_func="check_process",
            scene_id=str(self.scene_id),
            parameter_id=str(self.traffic_event.id),
            script_args=json.dumps(parameter),
            trigger_args=json.dumps({
                "delay": delay_time,
                "seconds": 10,
            }),
            report_url="http://169.254.169.254/cr/api/traffic_event/agents/"
        )


class BackgroundTrafficManager(BaseTraffic):
    def _run(self, data, agent_client, extra_params):
        params = {'dst_ip': data.get('target_ip'), 'dst_mac': data.get('target_mac')}
        params.update(extra_params)
        return agent_client.execute_script(self.script_path, main_func="traffic", json_args=json.dumps(params))

    def _handle_event_status(self, message):
        if message.get('content'):
            msg = message.get('content')
            self.logger.debug("TrafficEvent[%s]-tcpreplay: %s", self.traffic_event.title, msg)
            if msg != "" and msg.get('status') == 'ok':
                self.traffic_event.status = TrafficEvent.Status.RUNNING
                self.traffic_event.error = ""
                self.traffic_event.pid = msg.get('pid')
                self.logger.info("TrafficEvent[%s]: run success", self.traffic_event.title)

            if msg != "" and msg.get('status') == 'error' and msg.get('msg'):
                self.traffic_event.status = TrafficEvent.Status.ERROR
                self.traffic_event.error = msg.get('msg')
                self.traffic_event.pid = ''
                self.logger.error("TrafficEvent[%s] running error: %s", self.traffic_event.title, msg.get('msg'))

            self.traffic_event.save()
            return msg
        else:
            return None


class IntelligentTrafficManager(BaseTraffic):
    def _run(self, data, agent_client, extra_params):
        # checked in parent class
        if self.script_path.split(".")[-1] == "py":
            params = {'ip': data.get('target_ip')}
            params.update(extra_params)
            return agent_client.execute_script(self.script_path, main_func="traffic", json_args=json.dumps(params),
                                               sync=False)
        else:
            parameter_str = str(data.get("target_ip"))
            for key in extra_params:
                parameter_str += " " + str(extra_params[key])

            return agent_client.execute_script(self.script_path, json_args=json.dumps(parameter_str), sync=False)

    def _handle_event_status(self, message):
        self.logger.debug("TrafficEvent[%s]-script: %s", self.traffic_event.title, message)
        self.traffic_event.status = TrafficEvent.Status.RUNNING
        if message.get('pid'):
            parent_pid = int(message.get('pid'))
            self.traffic_event.pid = parent_pid + 1

        if message.get('content'):
            msg = {'status': 'ok', 'msg': message.get('content')}
        else:
            msg = {'status': 'ok', 'msg': 'script run success'}
        self.traffic_event.error = ""
        self.traffic_event.save()
        self.logger.info("TrafficEvent[%s]: is running", self.traffic_event.title)
        return msg
