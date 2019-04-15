# -*- coding: utf-8 -*-
from base.utils.rpc.client import AgentClient
import json
import logging

system_logger = logging.getLogger(__name__)


class RpcThrift(object):

    def thrift_client(self, host, port):
        try:
            check_func = AgentClient(host, port)
            return check_func
        except Exception as e:
            system_logger.error(e)


class ScriptClient(RpcThrift):
    def __init__(self, logger, content, script_url=None):
        self.logger = logger
        self.content = content
        self.script_url = script_url

    def py_script_check(self, **kwargs):

        parameter = {"ip": self.content.get("target_ip")}
        if kwargs:
            parameter.update(kwargs)

        self.logger.info("Python Checker ip :[%s], Python Checker port :[%d]",
                         self.content.get("checker_ip"), self.content.get("checker_port"))
        self.logger.info("Python Parameter: [%s]", parameter)

        check_func = self.thrift_client(self.content.get("checker_ip"), self.content.get("checker_port"))

        _ret = check_func.execute_script(self.script_url, main_func="checker",
                                         json_args=json.dumps(parameter))
        return _ret

    def sh_script_check(self, **kwargs):
        parameter_str = str(self.content.get("target_ip"))
        if kwargs:
            for key in kwargs:
                parameter_str = parameter_str + " " + str(kwargs[key])

        self.logger.debug("Shell Checker ip :[%s], Shell Checker port :[%d], Shell Parameter: [%s]",
                          self.content.get("checker_ip"), self.content.get("checker_port"), parameter_str)

        check_func = self.thrift_client(self.content.get("checker_ip"), self.content.get("checker_port"))
        _ret = check_func.execute_script(self.script_url, json_args=json.dumps(parameter_str))

        return _ret

    def agent_python_check(self, **kwargs):
        parameter = {"ip": self.content.get("target_ip")}
        if kwargs:
            parameter.update(kwargs)

        self.logger.info("Python Checker ip :[%s], Python Checker port :[%d]",
                         self.content.get("checker_ip"), self.content.get("checker_port"))
        self.logger.info("Python Parameter: [%s]", parameter)

        check_func = self.thrift_client(self.content.get("checker_ip"), self.content.get("checker_port"))
        try:
            version = check_func.version()
            self.logger.info('RPC version[%s]', version)
            if version.get("status") == 'down':
                self.logger.error("Link not on RPC")
                return False
            elif version.get("status") == 'error':
                self.logger.error("RPC error")
                return False
            else:
                self.agent_python_client(check_func, parameter)
                return True
        except Exception as e:
            self.logger.error("RPC error:%s", e)

    def agent_shell_check(self, **kwargs):
        parameter_str = str(self.content.get("target_ip"))
        if kwargs:
            for key in kwargs:
                parameter_str = parameter_str + " " + str(kwargs[key])

        self.logger.info("Shell Checker ip :[%s], Shell Checker port :[%d]",
                         self.content.get("checker_ip"), self.content.get("checker_port"))
        self.logger.info("Shell Parameter: [%s]", parameter_str)

        check_func = self.thrift_client(self.content.get("checker_ip"), self.content.get("checker_port"))

        try:
            version = check_func.version()
            self.logger.info('RPC version[%s]', version)
            if version.get("status") == 'down':
                self.logger.error("Link not on RPC")
                return False
            elif version.get("status") == 'error':
                self.logger.error("RPC error")
                return False
            else:
                self.agent_shell_client(check_func, parameter_str)
                return True
        except Exception as e:
            self.logger.error("RPC error: %s", e)

    def agent_python_client(self, check_func, parameter):
        self.logger.info(self.script_url)
        if self.content.get("is_once"):
            check_func.scheduler_execute_script(
                self.script_url,
                main_func="checker",
                scene_id=str(self.content.get("scene_id")),
                parameter_id=str(self.content.get("id")),
                script_args=json.dumps(parameter),
                report_url="http://169.254.169.254/cr/api/mission/agents/"
            )
        else:
            check_func.scheduler_execute_script(
                self.script_url, main_func="checker",
                scene_id=str(self.content.get("scene_id")),
                parameter_id=str(self.content.get("id")),
                script_args=json.dumps(parameter),
                trigger_args=json.dumps({
                    "delay": self.content.get("first_check_time", 0),
                    "seconds": self.content.get("interval", 0)
                }),
                report_url="http://169.254.169.254/cr/api/mission/agents/"
            )

    def agent_shell_client(self, check_func, parameter_str):
        self.logger.info(self.script_url)
        if self.content.get("is_once"):
            check_func.scheduler_execute_script(
                self.script_url,
                script_args=json.dumps(parameter_str),
                scene_id=str(self.content.get("scene_id")),
                parameter_id=str(self.content.get("id")),
                main_func="checker",
                report_url="http://169.254.169.254/cr/api/mission/agents/",
            )
        else:
            check_func.scheduler_execute_script(
                self.script_url,
                script_args=json.dumps(parameter_str),
                scene_id=str(self.content.get("scene_id")),
                parameter_id=str(self.content.get("id")),
                trigger_args=json.dumps({
                    "delay": self.content.get("first_check_time", 0),
                    "seconds": self.content.get("interval", 0)
                }),
                report_url="http://169.254.169.254/cr/api/mission/agents/"

            )

    def stop_agent_client(self):

        self.logger.info("Stop Agent ip :[%s: %s] : Starting", self.content.get("checker_ip"),
                         self.content.get("checker_port"))
        check_func = self.thrift_client(self.content.get("checker_ip"), self.content.get("checker_port"))
        _ret = check_func.scheduler_job_action(str(self.content.get("scene_id")), str(self.content.get("id")), "remove")
        self.logger.info("Stop agent mission return: %s", _ret)
