# coding: utf-8
import os

import time
from datetime import datetime
from django.core.management import BaseCommand

from base_cloud import app_settings
from base_cloud.clients import nova_client
from dashboard.cms.views import Hypervisor
from dashboard.models import SystemUseStatus

last_worktime = 0
last_idletime = 0


def get_cpu():
    global last_worktime, last_idletime
    f = open("/proc/stat", "r")
    line = ""
    while "cpu " not in line:
        line = f.readline()
    f.close()
    spl = line.split(" ")
    worktime = int(spl[2]) + int(spl[3]) + int(spl[4])
    idletime = int(spl[5])
    dworktime = (worktime - last_worktime)
    didletime = (idletime - last_idletime)
    rate = float(dworktime) / (didletime + dworktime)
    last_worktime = worktime
    last_idletime = idletime
    if last_worktime == 0:
        return 0
    return rate


def get_mem_usage_percent():
    try:
        f = open('/proc/meminfo', 'r')
        for line in f:
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1])
            elif line.startswith('MemFree:'):
                mem_free = int(line.split()[1])
            elif line.startswith('Buffers:'):
                mem_buffer = int(line.split()[1])
            elif line.startswith('Cached:'):
                mem_cache = int(line.split()[1])
            elif line.startswith('SwapTotal:'):
                vmem_total = int(line.split()[1])
            elif line.startswith('SwapFree:'):
                vmem_free = int(line.split()[1])
            else:
                continue
        f.close()
    except Exception:
        return None
    physical_percent = usage_percent(mem_total - (mem_free + mem_buffer + mem_cache), mem_total)
    virtual_percent = 0
    if vmem_total > 0:
        virtual_percent = usage_percent((vmem_total - vmem_free), vmem_total)
    return physical_percent, virtual_percent


def usage_percent(use, total):
    try:
        ret = (float(use) / total) * 100
    except ZeroDivisionError:
        raise Exception("ERROR - zero division error")
    return ret


class Command(BaseCommand):

    def sys_status(self):
        cpu_allocation_ratio = app_settings.COMPLEX_MISC.get("cpu_allocation_ratio", 16.0)
        ram_allocation_ratio = app_settings.COMPLEX_MISC.get("ram_allocation_ratio", 1.5)
        disk_allocation_ratio = app_settings.COMPLEX_MISC.get("disk_allocation_ratio", 1.0)
        hyperv_list = []
        context = {}
        instance_count = 0
        vcpu_percent = 0.0
        ram_percent = 0.0
        disk_percent = 0.0
        try:
            nv_client = nova_client.Client(project_name="admin")
            hypers = nv_client.hypervisor_list()

            for hyper in hypers:
                container_count = 0

                instance_count += hyper.running_vms
                hyper.vcpus = hyper.vcpus * cpu_allocation_ratio
                vcpu_percent += float(hyper.vcpus_used) / float(hyper.vcpus)
                hyper.memory_mb = hyper.memory_mb * ram_allocation_ratio
                ram_percent += float(hyper.memory_mb_used) / float(hyper.memory_mb)
                hyper.local_gb = hyper.local_gb * disk_allocation_ratio
                disk_percent += float(hyper.local_gb_used) / float(hyper.local_gb)

                hyper_dict = Hypervisor(hyper).to_dict()
                hyper_dict['container_count'] = container_count
                hyperv_list.append(hyper_dict)
            hyper_count = len(hypers)
            context.update({"cluster_state": {
                "vms": instance_count,
                "vcpu": vcpu_percent / hyper_count * 100,
                "ram": ram_percent / hyper_count * 100,
                "disk": disk_percent / hyper_count * 100,
            }})
        except Exception:
            pass
        context.update({"hypervisors": hyperv_list})
        return context

    def get_local_usage(self):

        context = {}
        statvfs = os.statvfs('/')
        total_disk_space = statvfs.f_frsize * statvfs.f_blocks
        free_disk_space = statvfs.f_frsize * statvfs.f_bfree
        disk_usage = (total_disk_space - free_disk_space) * 100.0 / total_disk_space
        disk_usage = int(disk_usage)
        mem_usage = get_mem_usage_percent()
        mem_usage = int(mem_usage[0])
        cpu_usage = int(get_cpu() * 100)
        context.update({"cluster_state": {
            "vcpu": cpu_usage,
            "ram": mem_usage,
            "disk": disk_usage,
        }})
        return context

    def handle(self, *args, **options):

        while True:
            datas = self.get_local_usage()["cluster_state"]
            sys_use_status = SystemUseStatus.objects.create(
                alert_time=datetime.now(),
                vcpu=datas["vcpu"],
                ram=datas["ram"],
                disk=datas["disk"]
            )
            sys_use_status.save()
            time.sleep(60)
