# -*- coding: utf-8 -*-
import os
import random

from django.core.cache import cache
from django.utils import timezone

from base.utils.text import rk

from base_cloud import api as cloud
from base_cloud.clients.glance_client import Client as GlanceClient

from base_scene import app_settings
from base_scene.models import Disk


def random_cidr():
    return '%s.%s.0/24' % (random.choice(app_settings.SCENE_SUBNET_SEG), random.randint(16, 100))


def random_cidrs(count, exclude_cidrs=None):
    third_range = range(16, 100)
    cidr_pools = []
    for subnet_seg in app_settings.SCENE_SUBNET_SEG:
        for third_number in third_range:
            cidr = '%s.%s.0/24' % (subnet_seg, third_number)
            if not exclude_cidrs or cidr not in exclude_cidrs:
                cidr_pools.append(cidr)
    if count > len(cidr_pools):
        raise Exception('too many cidrs to allocate')
    return random.sample(cidr_pools, count)


def random_ips(cidr, count, exclude_ips=None):
    ip_pools = []
    prefix = cidr[:-4]
    for forth_number in range(100, 200):
        ip_pools.append('%s%s' % (prefix, str(forth_number)))
    if exclude_ips:
        ip_pools = list(set(ip_pools) - set(exclude_ips))
    if count > len(ip_pools):
        raise Exception('no more ip')
    return random.sample(ip_pools, count)


def random_password(len=8):
    return "".join(random.sample('23456789abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ', len))


def is_external_net(net_id):
    return net_id.lower().startswith(app_settings.EXTERNAL_NET_ID_PREFIX)


# 转换成预估的剩余秒数
def get_part_seconds(create_time, consume_seconds):
    loaded_time = timezone.now() - create_time
    loaded_seconds = int(loaded_time.total_seconds())

    if consume_seconds is None:
        return loaded_seconds, None

    remain_seconds = consume_seconds - loaded_seconds
    return loaded_seconds, remain_seconds


def get_base_images():
    base_images = cache.get('openstack_base_images') or []
    if base_images:
        return base_images

    images = GlanceClient().image_get_all()
    for image in images:
        if image.name in app_settings.BASE_IMAGES:
            base_images.append(app_settings.BASE_IMAGE_MAPPING[image.name])

    base_images.sort(key=lambda x: app_settings.BASE_IMAGES.index(x['name']))
    cache.set('openstack_base_images', base_images, None)

    return app_settings.BASE_IMAGES


def attach_disk(server_id, disk_id):
    cloud.volume.attach_volume(disk_id, server_id)
    Disk.objects.filter(disk_id=disk_id).update(status=Disk.Status.USING)


def detach_disk(server_id, disk_id):
    cloud.volume.detach_volume(server_id, disk_id)
    Disk.objects.filter(disk_id=disk_id).update(status=Disk.Status.AVAILABLE)


def mount_disk(disk_id):
    mnt_dir = os.path.join(app_settings.DISK_MNT_DIR, rk())
    cloud.volume.mount(disk_id, mnt_dir)
    try:
        Disk.objects.filter(disk_id=disk_id).update(mnt_dir=mnt_dir)
    except Exception:
        cloud.volume.umount(mnt_dir, remove_dir=True)
    else:
        return mnt_dir


def umount_disk(disk_id):
    try:
        mnt_dir = Disk.objects.filter(disk_id=disk_id).values('mnt_dir')[0]['mnt_dir']
    except Exception:
        return

    cloud.volume.umount(mnt_dir, remove_dir=True)
    Disk.objects.filter(disk_id=disk_id).update(mnt_dir=None)
