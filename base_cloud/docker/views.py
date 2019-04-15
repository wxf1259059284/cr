from __future__ import unicode_literals

import functools
import logging
import os
import subprocess
import time
import uuid

from django.utils.translation import ugettext as _

from base.utils.functional import cached_property
from base_cloud.clients.zun_client import Client as zun_client
from base_cloud.exception import FriendlyException
from base_cloud.utils import get_ip_by_hostname

ATTEMPTS = 900
LOG = logging.getLogger(__name__)
states = {
  'ERROR': 'Error', 'RUNNING': 'Running', 'STOPPED': 'Stopped',
  'PAUSED': 'Paused', 'UNKNOWN': 'Unknown', 'CREATING': 'Creating',
  'CREATED': 'Created', 'DELETED': 'Deleted'
}


def logger_decorator(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        func_name = func.__name__
        LOG.debug("Start {}(): args={}, kwargs={}".format(func_name,
                                                          args, kwargs))
        ff = func(self, *args, **kwargs)
        LOG.debug("End {}()".format(func_name))
        return ff
    return wrapper


def clean_create_params(func):
    @functools.wraps(func)
    def wrapper(self, **kwargs):
        body = {}
        body['name'] = kwargs.get("name")

        return func(self, **kwargs)
    return wrapper


class ContainerAction(object):
    def __init__(self):
        super(ContainerAction, self).__init__()

    @cached_property
    def zun_cli(self):
        return zun_client()

    def _handle_error(self, err_msg=None, e=None):
        if not err_msg:
            err_msg = _("Unknown error occurred, Please try again later.")
        if e:
            err_msg = "{}\n{}".format(err_msg, getattr(e, "message", ""))
        LOG.error(err_msg)
        raise FriendlyException(err_msg)

    @logger_decorator
    def create_container(self, **kwargs):
        try:
            return self.zun_cli.container_create(**kwargs)
        except Exception as e:
            err_msg = _("Unable to create container {}").format(kwargs.get("name"))
            self._handle_error(err_msg, e)

    @logger_decorator
    def check_container_status(self, cont):
        cont_id = cont.uuid
        cont_name = cont.name or cont_id

        attempts = ATTEMPTS
        while 1:
            if attempts <= 0:
                err_msg = _("Failed to check status for container {}: "
                            "The maximum number of attempts "
                            "has been exceeded.").format(cont_name)
                break
            container = self.zun_cli.container_show(cont_id)
            if container.status == states['RUNNING']:
                msg = "Container {} status Running.".format(cont_name)
                LOG.info(msg)
                setattr(container, "host_ip_address", get_ip_by_hostname(container.host))
                return container
            elif container.status == states['ERROR']:
                err_msg = _("Container {} status error."
                            " {}").format(cont_name, container.status_reason)
                break
            LOG.debug("Container status not active. "
                      "Try again 1 second later...")
            attempts -= 1
            time.sleep(1)
        self._handle_error(err_msg)

    @logger_decorator
    def delete_container(self, container_id, sync=True, force=True):
        try:
            self.zun_cli.container_delete(container_id, force=force)
        except Exception as e:
            err_msg = _("Unable to delete container {}").format(container_id)
            self._handle_error(err_msg, e)

        if sync:
            attempts = ATTEMPTS
            while attempts:
                try:
                    self.zun_cli.container_show(container_id)
                except Exception as e:
                    LOG.info("Deleted container {}".format(container_id))
                    break
                attempts -= 1
                time.sleep(1)
        return True

    @logger_decorator
    def list_container(self, **kwargs):
        prefix = kwargs.pop("prefix") if "prefix" in kwargs else None
        try:
            containers = self.zun_cli.container_list(**kwargs)
        except Exception as e:
            err_msg = _("Unable to list container "
                        "by kwargs {}").format(kwargs)
            self._handle_error(err_msg, e)
        if prefix and containers:
            return [cont for cont in containers
                    if cont.name.startswith(prefix.strip())]
        return containers

    @logger_decorator
    def execute_container_cmd(self, container_id, command):
        try:
            self.zun_cli.container_execute(container_id, command)
        except Exception as e:
            err_msg = _("Unable to execute command {} "
                        "for container {}").format(command, container_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def start_container(self, container_id):
        try:
            return self.zun_cli.container_start(container_id)
        except Exception as e:
            err_msg = _("Unable to start container {}").format(container_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def stop_container(self, container_id):
        try:
            return self.zun_cli.container_stop(container_id)
        except Exception as e:
            err_msg = _("Unable to stop container {}").format(container_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def pause_container(self, container_id):
        try:
            return self.zun_cli.container_pause(container_id)
        except Exception as e:
            err_msg = _("Unable to pause container {}").format(container_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def unpause_container(self, container_id):
        try:
            return self.zun_cli.container_unpause(container_id)
        except Exception as e:
            err_msg = _("Unable to unpause container {}").format(container_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def restart_container(self, container_id):
        try:
            return self.zun_cli.container_restart(container_id)
        except Exception as e:
            err_msg = _("Unable to restart container {}").format(container_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def save_image(self, container_id, repository):
        if not repository:
            repository = str(uuid.uuid4())
        try:
            return self.zun_cli.container_commit(container_id, repository)
        except Exception as e:
            err_msg = _("Unable to save image for container {}").format(container_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_container(self, container_id, convert_host_ip=True):
        try:
            container = self.zun_cli.container_show(container_id)
            if convert_host_ip:
                setattr(container, "host_ip_address",
                        get_ip_by_hostname(container.host))
            return container
        except Exception as e:
            err_msg = _("Unable to get container {}").format(container_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def build_docker_file(self, path):
        if os.path.exists(path):
            folder, file_name = os.path.split(path)
            img_name = "{}.img".format(os.path.splitext(file_name)[0])
            build_cmd = "docker build -t {} " \
                        "-f {} .".format(file_name, img_name)
            build_process = subprocess.Popen(build_cmd,
                                             stdout=subprocess.PIPE,
                                             shell=True)
            stream_output = build_process.communicate()[0]
            return_code = build_process.returncode

            LOG.debug(stream_output)
            LOG.debug(return_code)
            if return_code == 0:
                return os.path.join(folder, img_name)

            self._handle_error(stream_output)
        err_msg = _("Docker file not exists {}").format(path)
        self._handle_error(err_msg)
