# -*- coding:utf-8 -*-
import json
import os
import hashlib
import urlparse

import thriftpy
from thriftpy.rpc import client_context

from django.conf import settings

from cr.settings import RPC_DEFAULT_HOST, RPC_DEFAULT_PORT, SOCKET_TIMEOUT, CONNECT_TIMEOUT


class AgentClient(object):
    def __init__(self, host=RPC_DEFAULT_HOST, port=RPC_DEFAULT_PORT):
        self.host = host
        self.port = port
        self.agent_thrift = thriftpy.load("base/utils/rpc/agent.thrift",
                                          module_name="agent_thrift")

    def check_func(self, func_name):
        """ check function registered in *.thrift

        :param func_name: function name
        :return: True or Flase
        """
        if func_name in self.agent_thrift.AgentService.thrift_services:
            return True
        return False

    def remote_execute(self, func_name, **params):
        """ execute remote function with given func_name and params

        :param func_name: remote function name
        :param params: params
        :return: executed result
        """
        if self.check_func(func_name):
            try:
                with client_context(self.agent_thrift.AgentService, self.host, self.port,
                                    socket_timeout=SOCKET_TIMEOUT, connect_timeout=CONNECT_TIMEOUT) as c:
                    result = getattr(c, func_name)(**params)

                    try:
                        return json.loads(result)
                    except Exception as e:
                        return result
            except Exception as e:
                return {'status': "down", "message": e}

    def version(self):
        """ display agent server version

        :return: version number
        """
        return self.remote_execute("version")

    def execute_command(self, command, sync=True):
        """ execute command on remote server

        :param command: command string
        :return: execute result
        """
        return self.remote_execute("run_command", command=command, sync=sync)

    def execute_command_async(self, command):
        """ execute command on remote server

        :param command: command string
        :return: execute result
        """
        self.remote_execute("run_command_async", command=command)

    def execute_script(self, file_path, main_func="", json_args="", sync=True):
        """ execute script file on remote server

        :param file_path: local script path
        :param main_func: main function, only work for python script
        :param json_args: args string for scirpt file or main_func
        :return:
        """
        if file_path.startswith("http://"):
            urlp = urlparse.urlparse(file_path)
            content = file_path
            file_name = urlp.path.split("/")[-1]
            with open(os.path.join("/tmp", file_name), 'rb') as f:
                file_content = f.read()
            md5 = hashlib.md5()
            md5.update(file_content)
            checksum = md5.hexdigest()
        else:
            if not os.path.isfile(file_path):
                return None
            file_name = os.path.split(file_path)[1]

            with open(file_path, 'rb') as f:
                content = f.read()

            md5 = hashlib.md5()
            md5.update(content)
            checksum = md5.hexdigest()

        return self.remote_execute("run_script", name=file_name,
                                   content=content, checksum=checksum,
                                   main_func=main_func, json_args=json_args, sync=sync)

    def execute_script_async(self, file_path, main_func="", json_args=""):
        """ execute script file on remote server

        :param file_path: local script path
        :param main_func: main function, only work for python script
        :param json_args: args string for scirpt file or main_func
        :return:
        """
        if file_path.startswith("http://"):
            urlp = urlparse.urlparse(file_path)
            content = file_path
            file_name = urlp.path.split("/media/")[-1]
            with open(os.path.join(settings.BASE_DIR, file_name), 'rb') as f:
                file_content = f.read()
            md5 = hashlib.md5()
            md5.update(file_content)
            checksum = md5.hexdigest()
        else:
            if not os.path.isfile(file_path):
                return None
            file_name = os.path.split(file_path)[1]

            with open(file_path, 'rb') as f:
                content = f.read()

            md5 = hashlib.md5()
            md5.update(content)
            checksum = md5.hexdigest()

        return self.remote_execute("run_script_async", name=file_name,
                                   content=content, checksum=checksum,
                                   main_func=main_func, json_args=json_args)

    def scheduler_execute_script(self, file_path, scene_id="", parameter_id="", main_func="", script_args="",
                                 trigger_args="", report_url=""):
        """

        :param file_path: local script path
        :param script_args: args string for scirpt file
        :param trigger_args: (dict json string)args string for trigger
                    weeks (int) – number of weeks to wait
                    days (int) – number of days to wait
                    hours (int) – number of hours to wait
                    minutes (int) – number of minutes to wait
                    seconds (int) – number of seconds to wait
                    delay (int) – number of seconds to delay
                    start_date (datetime|str) – starting point for the interval calculation
                    end_date (datetime|str) – latest possible date/time to trigger on
                    timezone (datetime.tzinfo|str) – time zone to use for the date/time calculations
        :return: None
        """

        cr_event = scene_id
        machine_id = parameter_id
        if file_path.startswith("http://"):
            urlp = urlparse.urlparse(file_path)
            content = file_path
            file_name = urlp.path.split("/media/")[-1]
            with open(os.path.join(settings.BASE_DIR, file_name), 'rb') as f:
                file_content = f.read()
            md5 = hashlib.md5()
            md5.update(file_content)
            checksum = md5.hexdigest()
        else:
            if not os.path.isfile(file_path):
                return None
            file_name = os.path.split(file_path)[1]

            with open(file_path, 'rb') as f:
                content = f.read()

            md5 = hashlib.md5()
            md5.update(content)
            checksum = md5.hexdigest()

        return self.remote_execute("scheduler_run_script", cr_event=cr_event,
                                   machine_id=machine_id, name=file_name, content=content,
                                   checksum=checksum, main_func=main_func, script_args=script_args,
                                   trigger_args=trigger_args, report_url=report_url)

    def scheduler_job_action(self, cr_event, machine_id, action):
        """

        :param cr_event:
        :param machine_id:
        :param action: only support pause|resume|remove
        :return:
        """
        return self.remote_execute("scheduler_job_action", cr_event=cr_event,
                                   machine_id=machine_id, action=action)
