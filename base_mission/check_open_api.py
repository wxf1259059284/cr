# -*- coding: utf-8 -*-
import os

from base.utils.delete_channel_delay import delete_channel_delay
from base.utils.thread import async_exe
from base_mission import constant
from base_mission.check_api.connect_num_cache import ConnectCache
from base_mission.check_api.delivering_task import start_checker
from base_mission.check_api.misson_status import inquire_mission_status
from base_mission.check_api.parameter_validation import parameter_verification, ip_verification
from base_mission.check_api.rpc_client import ScriptClient
from base_mission.check_api.status_description import record_status_information
from base_mission.check_api.system_result_process import ResultProcess
from base_mission.models import Mission
from base_mission.utils.check_logger import SceneLogFactory
from base_mission.utils.object_attr import object_attr
from base_mission.constant import MissionStatus
from base_mission.check_api.get_script_parameter import kwargs_process

import logging

from cr import settings
from cr.config import MAX_BUMBER_ATTEMPTS
from cr_scene.utils import checker_info

logger_critical = logging.getLogger(__name__)


class MissionCheckerManager(object):
    def __init__(self, mission, cr_scene, scene_id):
        self.mission = mission
        self.cr_scene = cr_scene
        self.scene_id = scene_id
        self.logger = SceneLogFactory(self.scene_id, __name__)

    # no_delay是否有延迟的执行， 为True的时候是立即执行
    def start(self, no_delay=False):
        # 更改mission的状态
        record_status_information(
            self.mission,
            "Start up mission check",
            constant.MissionStatus.ISPROCESS)

        # 参数处理
        script_data = self._param_check()

        if script_data is None or script_data == {}:
            record_status_information(
                self.mission,
                "Parameter detection does not pass",
                constant.MissionStatus.ERROR)
            self.logger.error("Mission[%s]: Parameter detection does not pass", self.mission.title)
        else:
            # 发布任务
            self.logger.info("Mission[%s]: Publish mission", self.mission.title)
            start_checker(script_data, self.logger, no_delay)

    def stop(self):
        # 更改Mission状态是停止
        record_status_information(
            self.mission,
            "Has stopped check",
            constant.MissionStatus.STOP)

        delete_channel_delay({"id": self.mission.id})

        self.logger.info("Mission[%s]: Has stopped check", self.mission.title)

    def _param_check(self):
        """
        参数验证，是否完整
        :return:
        """
        data = self._data_process()

        self.logger.debug("Mission[%s]: data:[%s]", self.mission.title, data)

        if data == {}:
            self.logger.error("Mission[%s]: missing parameters", self.mission.title)

        return data

    def _data_process(self):
        """
        处理数据，获取所需参数
        :return:
        """
        parameter_list = ["id", "score", "title"]
        check_mission_list = ["interval", "is_once", "is_polling",
                              "first_check_time", "scripts", "check_type",
                              "checker_id", "target_net",
                              "target"]

        self.logger.debug("Mission[%s]: Data process start", self.mission.title)

        check_mission = object_attr(self.mission, "checkmission")
        obj_data = parameter_verification(self.mission, parameter_list)

        if check_mission.check_type == constant.CheckType.AGENT:
            check_mission_list.remove("checker_id")
            check_mission_list.remove("target_net")

        check_mission_data = parameter_verification(check_mission, check_mission_list)

        if {} in [obj_data, check_mission_data]:
            self.logger.error("Mission[%s]: Parameter verification failed", self.mission.title)
            return obj_data

        script = check_mission_data.get("scripts")

        # 获取checker_ip， port， target_ip, 并验证
        target_id = check_mission_data.get("target")
        checker_id = check_mission_data.get("checker_id")
        target_net_id = check_mission_data.get("target_net")

        self.logger.debug("Mission[%s]: target_id[%s], checker_id[%s], target_net_id[%s]", self.mission.title,
                          target_id, checker_id, target_net_id)
        if checker_id is None or target_net_id is None:
            checker_ip, port = checker_info.get_checker_ip(self.cr_scene.id, target_id)
            target_ip = checker_ip
        else:
            checker_ip, port = checker_info.get_checker_ip(self.scene_id, checker_id)
            target_ip = checker_info.get_terminal_ip(self.scene_id, target_id, target_net_id)

        self.logger.debug("Mission[%s]: target_ip[%s], checker_ip[%s], port[%s]",
                          self.mission.title, target_ip, checker_ip, port)

        if checker_ip is None or port is None:
            self.logger.error("Mission[%s]: get checker ip[%s] or port[%s] error",
                              self.mission.title, checker_ip, port)
            return {}

        else:
            if len(checker_ip) == 0 or port == 0:
                self.logger.error("Mission[%s]: get checker ip[%s] or port[%d] error",
                                  self.mission.title, checker_ip, port)
                return {}

        if not ip_verification(checker_ip) or not ip_verification(target_ip):
            self.logger.error("Mission[%s]: target ip[%s] or checker ip[%s] error",
                              self.mission.title, checker_ip, port)

            return {}

        data = {
            "scene_id": self.scene_id,
            "scene_name": self.cr_scene.name,
            "checker_ip": checker_ip,
            "target_ip": target_ip,
            "checker_port": port,
            "script": script
        }

        data.update(obj_data)
        data.update(check_mission_data)

        mission_params = object_attr(check_mission, "params")
        if mission_params:
            data = kwargs_process(data, mission_params)

        return data


class MissionRpcCheckerManager(MissionCheckerManager):
    def stop(self):
        super(MissionRpcCheckerManager, self).stop()


class MissionAgentCheckerManager(MissionCheckerManager):
    def stop(self):
        super(MissionAgentCheckerManager, self).stop()

        target_id = object_attr(self.mission, 'target')

        self.logger.debug("Mission[%s]: get target sud_id: %s", self.mission.title, target_id)

        checker_ip, port = checker_info.get_checker_ip(self.scene_id, target_id)
        self.logger.info("[Stop Agent Mission] Mission[%s]: get checker ip: [%s] , port: [%s]",
                         self.mission.title, checker_ip, port)
        if checker_ip is None or port is None or target_id is None:
            self.logger.error("[Stop Agent Mission] Mission[%s]: get checker ip[%s] or port[%s] error",
                              self.mission.title, checker_ip, port)
            record_status_information(
                self.mission,
                "Stop agent mission error, get checker ip or port is error".format(title=self.mission.title),
                constant.MissionStatus.ERROR)
        else:

            data = {
                "checker_ip": checker_ip,
                "checker_port": port,
                "scene_id": self.cr_scene.id,
                "id": self.mission.id
            }
            script_client = ScriptClient(self.logger, data)
            script_client.stop_agent_client()
            ConnectCache(self.cr_scene.id, self.mission.id).blank_cache()


class BaseChecked(object):
    def __init__(self, content):
        self.content = content
        self.logger = SceneLogFactory(content.get("scene_id", "default"), __name__)

        self.mission_connect_cache = ConnectCache(content.get("scene_id"), content.get("id"))

    def run(self):
        # 检测参数
        message_parameter_list = ["scene_id", "script", "id", "check_type",
                                  "first_check_time", "target_ip", "checker_ip",
                                  "is_polling", "title", "score", "is_once",
                                  "interval", "checker_port", "scene_name"]
        parameter = parameter_verification(self.content, message_parameter_list)
        if not parameter:
            self.logger.error("Mission[%s]: Parameter Missing", self.content.get("title"))
            if self.content.get("id"):
                record_status_information(self.content.get("id"), "Parameter Missing", MissionStatus.ERROR)
            else:
                self.logger.error("No mission id")

        # 验证脚本是否存在
        script = self.content.get('script')
        script_url = settings.BASE_DIR + "/media/scripts/mission/{mission_id}/{script}".format(
            mission_id=self.content.get("id"),
            script=script)
        self.logger.debug("Mission[%s]: script path: %s", self.content.get("title"), script_url)
        if not os.path.exists(script_url):
            self.logger.error("Mission[%s] script[%s]: script does not exist", self.content.get("title"), script)

            record_status_information(self.content.get("id"), "script does not exist", MissionStatus.ERROR)

        script_client = ScriptClient(self.logger, self.content, script_url)

        # 验证状态
        mission_status = inquire_mission_status(self.content.get('id'))
        if mission_status == MissionStatus.ISPROCESS or mission_status == MissionStatus.DOWN:
            kwargs = self.content.get('kwargs', {})
            self._run(script, script_client, **kwargs)

    def _run(self, script, script_client, **kwargs):
        raise NotImplementedError("implement in sub class")


class RpcChecked(BaseChecked):

    def _run(self, script, script_client, **kwargs):
        self.logger.info("Mission[%s] : The parameter check is completed， RPC check start", self.content.get("title"))

        if script.split(".")[-1] == "py":
            _ret = script_client.py_script_check(**kwargs)
        else:
            _ret = script_client.sh_script_check(**kwargs)

        self.logger.debug("Mission[%s]: Check result: %s", self.content.get("title"), _ret)

        mission_connect_number = self.mission_connect_cache.set_frequency_cache(_ret.get("status"))
        # set the cache based on the results
        if mission_connect_number <= MAX_BUMBER_ATTEMPTS:
            mission = Mission.objects.filter(id=self.content.get("id")).first()
            mission_status = mission.mission_status
            if mission_status != MissionStatus.STOP:
                _result = ResultProcess(self.content, _ret)
                _result.check_over(mission)
        else:
            record_status_information(
                self.content.get("id"),
                "Check has stopped connecting,"
                "because the number of attempts to connect has reached the maximum",
                constant.MissionStatus.DOWN
            )
            self.logger.info("Mission[%s]:Check has stopped connecting,"
                             "because the number of attempts to connect has reached the maximum",
                             self.content.get("title"))


class AgentChecked(BaseChecked):

    def _run(self, script, script_client, **kwargs):
        self.logger.info("Mission[%s]: The parameter check is completed， Agent check start",
                         self.content.get("title"))
        if script.split(".")[-1] == "py":
            is_run = script_client.agent_python_check(**kwargs)
        else:
            is_run = script_client.agent_shell_check(**kwargs)

        if is_run:
            self.mission_connect_cache.blank_cache()  # cache set to 0 when the connection is successful
            record_status_information(
                self.content.get("id"),
                "Agent check is running",
                constant.MissionStatus.ISPROCESS
            )
            self.logger.info("Mission[%s]: Agent check is running", self.content.get("title"))
        else:
            mission_connect_number = self.mission_connect_cache.set_frequency_cache()  # Connect failed,set cache
            if mission_connect_number <= MAX_BUMBER_ATTEMPTS:
                self.logger.info("Mission[%s]: Agent check unable to connect", self.content.get("title"))
                mission = Mission.objects.filter(id=self.content.get("id")).first()
                mission_status = mission.mission_status
                if mission_status != MissionStatus.STOP:
                    async_exe(start_checker, (self.content,), delay=5)
            else:
                record_status_information(
                    self.content.get("id"),
                    "Agent has stopped connecting,"
                    " because the number of attempts to connect has reached the maximum",
                    constant.MissionStatus.DOWN
                )
                self.logger.info("Mission[%s]: Agent has stopped connecting,"
                                 "because the number of attempts to connect has reached the maximum",
                                 self.content.get("title"))
