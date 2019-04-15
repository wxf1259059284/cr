
import json
import logging

from base.utils.functional import cached_property
from base.utils.text import rk
from base.utils.thread import async_exe


from base_proxy import app_settings as proxy_settings
from base_cloud import api as cloud
from base_scene import app_settings
from base_scene.models import StandardDevice, SceneTerminal, StandardDeviceSnapshot

from .exceptions import SceneException
from .error import error
from .single_scene import SingleSceneHandler


logger = logging.getLogger(__name__)


class BaseHandler(object):

    def __init__(self, user, device, **kwargs):
        self.user = user
        self.device = device
        self.proxy = kwargs.get('proxy', True) and proxy_settings.SWITCH
        self.remote = kwargs.get('remote', True)

    def __call__(self, device=None):
        self.device = device

        if hasattr(self, 'reset_cached_propertys'):
            self.reset_cached_propertys()

        return self

    @cached_property
    def single_scene_handler(self):
        return SingleSceneHandler(self.user, proxy=self.proxy, remote=self.remote, scene=self.device.image_scene)

    @cached_property
    def scene_handler(self):
        return self.single_scene_handler.scene_handler

    @cached_property
    def scene_terminal(self):
        return self.single_scene_handler.scene_terminal

    @cached_property
    def image_status_updated(self):
        if self.device.image_status_updated:
            status_updated = self.device.image_status_updated.execute
        else:
            status_updated = None

        def _wrapper(*args, **kwargs):
            if status_updated:
                async_exe(status_updated, args=args, kwargs=kwargs)
        return _wrapper


class GetMixin(object):

    def get_image_scene(self):
        if not self.device.image_scene:
            return None

        data = self.single_scene_handler.get()
        data['id'] = self.device.image_scene_id
        return data

    def get_console_url(self):
        if not self.device.image_scene:
            return None

        return self.single_scene_handler.get_console_url()


class CreateMixin(object):

    def create_image(self, image_name, created=None, failed=None):
        device = self.device

        if not device.image_scene:
            raise SceneException(error.DEVICE_NO_SCENE)

        def image_created(image):
            logger.info('device[%s] image created', device.name)
            device.image_status = StandardDevice.ImageStatus.CREATED
            try:
                device.save()
            except Exception as e:
                logger.error('save device[%s] error: %s', device.name, e)

            try:
                self.delete_image_scene()
            except Exception as e:
                logger.error('delete device[%s] image scene error: %s', device.name, e)

            if created:
                created(image)

        def image_failed(error):
            logger.info('device[%s] image failed', device.pk)
            device.image_status = StandardDevice.ImageStatus.ERROR
            device.error = error
            try:
                device.save()
            except Exception as e:
                logger.error('save device[%s] error: %s', device.name, e)

            if failed:
                failed(error)

        terminal_util = self.scene_handler.get_terminal_util(self.scene_terminal)
        terminal_util.save_image(image_name=image_name, created=image_created, failed=image_failed)

    def create_image_scene(self, status_updated=None):
        device = self.device

        if device.image_scene:
            self.delete_image_scene(save=False)

        scene_config = get_image_scene_config(device)
        device.image_scene = self.single_scene_handler.create(scene_config, status_updated=status_updated)
        device.save()

        if hasattr(self, 'reset_cached_propertys'):
            self.reset_cached_propertys()


class DeleteMixin(object):

    def delete(self):
        device = self.device

        if device.image_scene:
            self.delete_image_scene(save=False)

        async_exe(cloud.image.delete, kwargs={'image_name': device.name})
        if device.image_type == StandardDevice.ImageType.VM:
            async_exe(cloud.image.operator.scene_delete_img_with_disk, kwargs={'image_name': device.name})
        device.name = device.name + rk()
        device.status = StandardDevice.Status.DELETE
        device.save()

    def delete_image_scene(self, save=True):
        device = self.device

        if device.image_scene:
            self.single_scene_handler.delete()
            device.image_scene = None
            if save:
                device.save()

            if hasattr(self, 'reset_cached_propertys'):
                self.reset_cached_propertys()


class DeviceHandler(GetMixin, CreateMixin, DeleteMixin, BaseHandler):
    pass


def get_standard_device_snapshot(device):
    return StandardDeviceSnapshot.objects.filter(
        standard_device=device
    ).order_by('-create_time').first()


def get_image_scene_config(device):
    snapshot = get_standard_device_snapshot(device)
    if snapshot:
        image_name = snapshot.name
    else:
        image = cloud.image.get(image_name=device.name)
        if image:
            image_name = device.name
        else:
            image_name = device.source_image_name

    scene = {
        'name': '%s_image_scene' % device.name,
    }
    routers = []
    networks = []
    server = {
        'id': device.name,
        'name': device.name,
        'imageType': device.image_type,
        'systemType': device.system_type,
        'systemSubType': device.system_sub_type,
        'image': image_name,
        'role': SceneTerminal.Role.OPERATOR,
        'flavor': device.flavor,
        'accessMode': [{
            'protocol': device.access_mode,
            'username': device.access_user,
            'password': device.access_password,
            'mode': device.access_connection_mode or '',
        }],
        'external': False,
        'net': []
    }

    try:
        gateway_port_configs = json.loads(device.gateway_port_configs)
    except Exception:
        gateway_port_configs = []

    if gateway_port_configs:
        server['external'] = True

        external_network = {
            'id': app_settings.EXTERNAL_NET_ID_PREFIX,
            'name': app_settings.EXTERNAL_NET_ID_PREFIX,
        }
        networks.append(external_network)

        router = {
            'id': 'router',
            'name': 'router',
            'net': [external_network['id']],
        }
        routers.append(router)

        gateway_port_configs.sort(key=lambda x: x.get('type', StandardDevice.GatewayPortType.LAN))
        for i, port_config in enumerate(gateway_port_configs):
            network = {
                'id': 'network_%s' % i,
                'name': 'lan_network_%s' % i,
            }
            cidr = port_config.get('cidr')
            if cidr:
                network['range'] = cidr

            networks.append(network)
            if i == 0:
                router['net'].append(network['id'])
            server['net'].append(network['id'])

    image_scene_config = {
        'json_config': {
            'scene': scene,
            'routers': routers,
            'networks': networks,
            'servers': [server],
        }
    }

    return image_scene_config
