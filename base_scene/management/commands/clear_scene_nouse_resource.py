# -*- coding: utf-8 -*-
import logging

from django.core.management import BaseCommand

from base.utils.models.common import clear_nouse_field_file
from base_cloud import api as cloud
from base_cloud.complex.views import BaseScene
from base_scene import app_settings
from base_scene.models import SceneNet, SceneGateway, SceneTerminal, Installer, InstallerResource
from base_scene.common.util.scene import using_status


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        clear_nouse_resource()
        clear_nouse_installer_file()


def _clear_resources(resource_ids, delete_func, base_queryset_infos, log_format):
    if resource_ids:
        using_resource_ids = []
        for base_queryset_info in base_queryset_infos:
            base_queryset = base_queryset_info[0]
            related_field = base_queryset_info[1]
            using_datas = base_queryset.filter(**{related_field + '__in': resource_ids})
            using_resource_ids.extend([getattr(using_data, related_field) for using_data in using_datas])
        not_use_resource_ids = list(set(resource_ids) - set(using_resource_ids))
        if not_use_resource_ids:
            logger.info(log_format % not_use_resource_ids)
            for resource_id in not_use_resource_ids:
                delete_func(resource_id)


# 清除没有被使用的虚拟资源
def clear_nouse_resource():
    logger.info('clear not use resources start')

    operator = BaseScene()
    # 清除场景相关的资源
    try:
        vms = operator.list_server(prefix=app_settings.BASE_GROUP_NAME)
        _clear_resources(
            [vm.id for vm in vms],
            cloud.vm.delete,
            [
                (SceneTerminal.objects.filter(scene__status__in=using_status, image_type=SceneTerminal.ImageType.VM),
                 'server_id'),
            ],
            'clear not use vm resources: not_use_vm_ids - %s'
        )
    except Exception as e:
        logger.error('clear not use vm resources error: %s' % str(e))

    try:
        dockers = operator.list_container(prefix=app_settings.BASE_GROUP_NAME)
        _clear_resources(
            [docker.id for docker in dockers],
            cloud.docker.delete,
            [
                (
                    SceneTerminal.objects.filter(
                        scene__status__in=using_status,
                        image_type=SceneTerminal.ImageType.DOCKER
                    ),
                    'server_id',
                ),
            ],
            'clear not use docker resources: not_use_docker_ids - %s'
        )
    except Exception as e:
        logger.error('clear not use docker resources error: %s' % str(e))

    try:
        routers = operator.list_router(prefix=app_settings.BASE_GROUP_NAME)

        _clear_resources(
            [router['id'] for router in routers],
            cloud.router.delete,
            [
                (SceneGateway.objects.filter(scene__status__in=using_status), 'router_id'),
            ],
            'clear not use router resources: not_use_router_ids - %s'
        )
    except Exception as e:
        logger.error('clear not use router resources error: %s' % str(e))

    try:
        firewalls = operator.list_firewall(prefix=app_settings.BASE_GROUP_NAME)
        _clear_resources(
            [firewall['id'] for firewall in firewalls],
            cloud.firewall.delete,
            [
                (SceneGateway.objects.filter(scene__status__in=using_status), 'firewall_id'),
            ],
            'clear not use firewall resources: not_use_firewall_ids - %s'
        )
    except Exception as e:
        logger.error('clear not use firewall resources error: %s' % str(e))

    try:
        networks = operator.list_network(prefix=app_settings.BASE_GROUP_NAME)
        _clear_resources(
            [network['id'] for network in networks],
            cloud.network.delete,
            [
                (SceneNet.objects.filter(scene__status__in=using_status), 'net_id'),
            ],
            'clear not use network resources: not_use_network_ids - %s'
        )
    except Exception as e:
        logger.error('clear not use network resources error: %s' % str(e))

    # 清除错误资源
    try:
        error_vms = operator.list_server(prefix=app_settings.BASE_GROUP_NAME,
                                         search_opts={'status': 'ERROR'})
        error_vm_ids = [error_vm.id for error_vm in error_vms]
        if error_vm_ids:
            logger.info('clear error resources: error_vm_ids - %s', error_vm_ids)
            for vm_id in error_vm_ids:
                cloud.vm.delete(vm_id)
    except Exception as e:
        logger.error('clear error vm resources error: %s' % str(e))

    try:
        dockers = operator.list_container(prefix=app_settings.BASE_GROUP_NAME)
        error_docker_ids = [docker.id for docker in dockers if docker.status.lower() == 'error']
        if error_docker_ids:
            logger.info('clear error resources: error_docker_ids - %s', error_docker_ids)
            for docker_id in error_docker_ids:
                cloud.docker.delete(docker_id)
    except Exception as e:
        logger.error('clear error docker resources error: %s' % str(e))

    logger.info('clear not use resources end')


# 清除没有被使用的安装文件
def clear_nouse_installer_file():
    using_resources = InstallerResource.objects.filter(installer__status=Installer.Status.NORMAL)
    clear_nouse_field_file(using_resources, 'file')
    clear_nouse_field_file(using_resources, 'encrypt_file')
