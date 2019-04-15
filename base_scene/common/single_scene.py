import json
import logging

from base.utils.functional import cached_property
from base_proxy import app_settings as proxy_settings
from base_scene.common.scene import SceneHandler
from base_scene.models import Disk


logger = logging.getLogger(__name__)


class BaseHandler(object):

    def __init__(self, user, **kwargs):
        self.user = user
        self.proxy = kwargs.get('proxy', True) and proxy_settings.SWITCH
        self.remote = kwargs.get('remote', True)
        self.scene = kwargs.get('scene', None)

    def __call__(self, scene=None):
        self.scene = scene

        if hasattr(self, 'reset_cached_propertys'):
            self.reset_cached_propertys()

        return self

    @cached_property
    def scene_handler(self):
        return SceneHandler(self.user, proxy=self.proxy, remote=self.remote, scene=self.scene)

    @cached_property
    def scene_terminal(self):
        return self.scene.sceneterminal_set.first()

    @cached_property
    def terminal_util(self):
        return self.scene_handler.get_terminal_util(self.scene_terminal)


class ControlMixin(object):

    def change_tunnel(self, tunnel):
        return self.terminal_util.change_tunnel(tunnel)

    def attach_disk(self, disk_ids):
        return self.terminal_util.attach_disk(disk_ids)

    def detach_disk(self, disk_ids):
        return self.terminal_util.detach_disk(disk_ids)


class GetMixin(object):

    def get(self):
        data = self.terminal_util.get_data()
        return data

    def get_disks(self):
        disk_ids = json.loads(self.scene_terminal.volumes)
        disks = Disk.objects.filter(disk_id__in=disk_ids)
        from base_scene.cms.serializers import DiskSerializer
        return DiskSerializer(disks, many=True).data

    def get_console_url(self):
        return self.terminal_util.get_console_url()

    def get_monitor_url(self):
        return self.terminal_util.get_monitor_url()

    def get_assistance_url(self):
        return self.terminal_util.get_assistance_url()


class CreateMixin(object):

    def create(self, scene_config, hang_info=None, status_updated=None):
        self.scene = self.scene_handler.create(scene_config, hang_info=hang_info, name_prefix='SS',
                                               status_updated=status_updated)
        return self.scene


class DeleteMixin(object):

    def delete(self, shutdown=False):
        self.scene_handler.delete(shutdown=shutdown)


class SingleSceneHandler(ControlMixin, GetMixin, CreateMixin, DeleteMixin, BaseHandler):
    pass
