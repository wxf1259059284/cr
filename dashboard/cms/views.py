# -*- coding: utf-8 -*-
import datetime
from django.http import JsonResponse
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from base_auth.models import User
from base_cloud import app_settings
from base_cloud.clients import nova_client
from base_mission.models import Mission
from base_scene.models import StandardDevice, Scene
from base_traffic.models import Traffic
from cr_scene import models as cr_scene_model
from dashboard.cms.serializers import DashSceneSerializer
from dashboard.models import SystemUseStatus

cpu_allocation_ratio = app_settings.COMPLEX_MISC.get("cpu_allocation_ratio", 16.0)
ram_allocation_ratio = app_settings.COMPLEX_MISC.get("ram_allocation_ratio", 1.5)
disk_allocation_ratio = app_settings.COMPLEX_MISC.get("disk_allocation_ratio", 1.0)


class Hypervisor(object):
    _attrs = ['cpu_info', 'host_ip', 'human_id', 'hypervisor_hostname',
              'hypervisor_type', 'id', 'memory_mb', 'memory_mb_used',
              'running_vms', 'state', 'status', 'vcpus', 'vcpus_used',
              'local_gb', 'local_gb_used']
    _hypervisor = None

    def __init__(self, hypervisor):
        self._hypervisor = hypervisor

    def to_dict(self):
        obj = {}
        for key in self._attrs:
            obj[key] = getattr(self._hypervisor, key, None)
        return obj


# dashboard 其他信息
@api_view(['GET'])
def dashboard(request):
    scenes = Scene.objects.all().order_by('-id')[:10]
    scene_data = DashSceneSerializer(scenes, many=True).data

    # openstack hypervisor
    hyperv_list = []
    try:
        instance_count = 0
        vcpu_percent = 0.0
        ram_percent = 0.0
        disk_percent = 0.0
        instance_max = 100
        nv_client = nova_client.Client(project_name="admin")
        hypers = nv_client.hypervisor_list()

        for hyper in hypers:
            hyperv_list.append(Hypervisor(hyper).to_dict())
            instance_count += hyper.running_vms
            vcpu_percent += float(hyper.vcpus_used) / float(hyper.vcpus)
            ram_percent += float(hyper.memory_mb_used) / float(hyper.memory_mb)
            disk_percent += float(hyper.local_gb_used) / float(hyper.local_gb)

        hyper_count = len(hypers)
    except Exception:
        return JsonResponse({})

    return Response(data={
        'scene_data': scene_data,
        "cluster_state": {
            "vms": instance_count,
            "vm_max": instance_max,
            "vcpu": vcpu_percent / hyper_count * 100 / cpu_allocation_ratio,
            "ram": ram_percent / hyper_count * 100 / ram_allocation_ratio,
            "disk": disk_percent / hyper_count * 100 / disk_allocation_ratio,
        },
        "hypervisors": hyperv_list,
    }, status=status.HTTP_200_OK)


# 获取平台用户人数,场景数
@api_view(['GET'])
def get_system_state(request):
    # 管理员 学员 教员
    users = User.objects.all()
    admin_user_count = 0
    ordinary_users_count = 0
    for user in users:
        if user.is_admin:
            admin_user_count += 1
        else:
            ordinary_users_count += 1

    user_data = [
        {"value": ordinary_users_count, "name": _('x_general_user')},
        {"value": admin_user_count, "name": _('x_administrator')},
    ]

    # 实例, 标靶 (虚拟机, 容器, 实体)
    cr_event_count = cr_scene_model.CrEvent.objects.count()
    cr_scene_count = cr_scene_model.CrScene.objects.count()
    standard_device_count = StandardDevice.objects.count()

    cr_event_data = [
        {"value": cr_event_count, "name": _('x_instance')},
        {"value": cr_scene_count, "name": _('x_scenes')},
        {"value": standard_device_count, "name": _('x_target')},
    ]

    traffic_count = Traffic.objects.count()
    mission_count = Mission.objects.count()

    base_data = [
        {"value": traffic_count, "name": _('x_flow')},
        {"value": mission_count, "name": _('x_task')},
    ]

    return JsonResponse({
        "user_data": user_data,
        "cr_event_data": cr_event_data,
        "base_data": base_data,
    })


# 获取cpu,内存,硬盘使用情况
@api_view(['GET'])
def get_system_used(request):
    x_axis = []
    cpu = []
    ram = []
    disk = []
    datas = SystemUseStatus.objects.order_by("-alert_time")[:100:-1]
    for data in datas:
        x_axis.append(datetime.datetime.strftime(data.alert_time, "%Y-%m-%d %H:%M:%S"))
        cpu.append(round(float(data.vcpu)))
        ram.append(round(float(data.ram)))
        disk.append(round(float(data.disk)))

    return JsonResponse({"x_axis": x_axis,
                         "CPUData": cpu,
                         "RAMData": ram,
                         "DISKData": disk,
                         })
