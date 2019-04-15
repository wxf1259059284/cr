from __future__ import unicode_literals

import logging
import subprocess

from keystoneauth1.identity import v3
from keystoneauth1 import session

from zunclient.common import utils
from zunclient.v1 import client

try:
    from base_cloud import app_settings
except Exception:
    pass

LOG = logging.getLogger(__name__)
CONTAINER_CREATE_ATTRS = client.containers.CREATION_ATTRIBUTES
IMAGE_PULL_ATTRS = client.images.PULL_ATTRIBUTES


class Client(object):
    def __init__(self, **kwargs):
        auth = v3.Password(
                auth_url=kwargs.get("auth_url") or app_settings.OS_AUTH.get("auth_url"),
                username=kwargs.get("username") or app_settings.OS_AUTH.get("username"),
                password=kwargs.get("password") or app_settings.OS_AUTH.get("password"),
                project_name=kwargs.get("project_name") or app_settings.OS_AUTH.get("project_name"),
                user_domain_id=kwargs.get("user_domain_id") or app_settings.OS_AUTH.get("user_domain_id"),
                project_domain_id=kwargs.get("project_domain_id") or app_settings.OS_AUTH.get("project_domain_id")
        )
        sess = session.Session(auth=auth)
        self.zun_client = client.Client(session=sess)

    def _cleanup_params(self, attrs, check, **params):
        args = {}
        run = False

        for (key, value) in params.items():
            if key == "run":
                run = value
            elif key == "cpu":
                args[key] = float(value)
            elif key == "memory":
                args[key] = int(value)
            elif key == "interactive" or key == "nets" \
                    or key == "security_groups" or key == "hints":
                args[key] = value
            elif key == "restart_policy":
                args[key] = utils.check_restart_policy(value)
            elif key == "environment" or key == "labels":
                values = {}
                vals = value.split(",")
                for v in vals:
                    kv = v.split("=", 1)
                    values[kv[0]] = kv[1]
                args[str(key)] = values
            elif key in attrs:
                if value is None:
                    value = ''
                args[str(key)] = str(value)
            elif check:
                LOG.error("Key must be in %s" % ",".join(attrs))

        return args, run

    def _delete_attributes_with_same_value(self, old, new):
        '''Delete attributes with same value from new dict

        If new dict has same value in old dict, remove the attributes
        from new dict.
        '''
        for k in old.keys():
            if k in new:
                if old[k] == new[k]:
                    del new[k]
        return new

    def container_list(self, limit=None, marker=None, sort_key=None,
                       sort_dir=None, detail=True):
        return self.zun_client.containers.list(limit, marker,
                                               sort_key, sort_dir)

    def container_show(self, id):
        return self.zun_client.containers.get(id)

    def container_logs(self, id):
        args = {}
        args["stdout"] = True
        args["stderr"] = True
        return self.zun_client.containers.logs(id, **args)

    def container_start(self, id):
        return self.zun_client.containers.start(id)

    def container_stop(self, id, timeout=10):
        return self.zun_client.containers.stop(id, timeout)

    def container_restart(self, id, timeout=10):
        return self.zun_client.containers.restart(id, timeout)

    def container_pause(self, id):
        return self.zun_client.containers.pause(id)

    def container_unpause(self, id):
        return self.zun_client.containers.unpause(id)

    def container_delete(self, id, force=False):
        return self.zun_client.containers.delete(id, force=force)

    def container_create(self, **kwargs):
        args, run = self._cleanup_params(CONTAINER_CREATE_ATTRS, True, **kwargs)
        if run:
            return self.zun_client.containers.run(**args)
        return self.zun_client.containers.create(**args)

    def container_update(self, id, **kwargs):
        container = self.zun_client.containers.get(id).to_dict()
        if container["memory"] is not None:
            container["memory"] = int(container["memory"].replace("M", ""))
        args, run = self._cleanup_params(CONTAINER_CREATE_ATTRS, True, **kwargs)

        # remove same values from new params
        self._delete_attributes_with_same_value(container, args)

        # do rename
        name = args.pop("name", None)
        if len(args):
            self.zun_client.containers.update(id, **args)

        # do update
        if name:
            self.zun_client.containers.rename(id, name)
            args["name"] = name
        return args

    def container_execute(self, id, command):
        args = {"command": command}
        return self.zun_client.containers.execute(id, **args)

    def container_kill(self, id, signal=None):
        return self.zun_client.containers.kill(id, signal)

    def container_attach(self, id):
        return self.zun_client.containers.attach(id)

    def container_commit(self, id, repository, tag=None):
        return self.zun_client.containers.commit(id, repository, tag=tag)

    def image_list(self, limit=None, marker=None, sort_key=None,
                   sort_dir=None, detail=True):
        return self.zun_client.images.list(limit, marker, sort_key, sort_dir, False)

    def image_build(self, image_name, docker_file_path):
        build_cmd = "docker build -t {}".format(image_name)
        p = subprocess.Popen(build_cmd, cwd=docker_file_path,
                             shell=True, stdout=subprocess.PIPE)
        output = p.communicate()
        p.wait()
        LOG.debug(output)

        if p.returncode == 0:
            return image_name
        return None

    def image_pull(self, **kwargs):
        args, run = self._cleanup_params(IMAGE_PULL_ATTRS, True, **kwargs)
        return self.zun_client.images.create(**args)

    def host_list(self):
        return self.zun_client.hosts.list()

    def service_list(self):
        return self.zun_client.services.list()

    def network_create(self, network_id):
        return self.zun_client.containers.network_create(network_id)


if __name__ == "__main__":
    cli = Client(auth_url="http://controller:35357/v3/", username="admin",
                 password="ADMIN_PASS", project_name="x-oj",
                 user_domain_id="default", project_domain_id="default")
