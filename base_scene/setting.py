# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .models import StandardDevice


# 场景配置文件名称
CONFIG_FILENAME = 'config.json'

# 平台id
PLATFORM_ID = 'platform'

# 外网前缀
EXTERNAL_NET_ID_PREFIX = 'internet'


# 标靶默认logo目录
DEFAULT_DEVICE_LOGO_DIR = 'standard_device_logo/default_device_logo/'


# 场景网络网段
SCENE_SUBNET_SEG = ['172.19']

# 创建的网络，路由，虚拟机等资源的组名，用以区分
BASE_GROUP_NAME = 'RC_SCENE'

WINDOWS_INSTALLER_DIR = 'C:\\Users\\Public'

LINUX_INSTALLER_DIR = '/tmp/tmp_installers'

DISK_MNT_DIR = os.path.join(settings.MEDIA_ROOT, 'mnt')

# docker并发创建锁时间
MAX_DOCKER_BLOCK_SECONDS = 20

# 终端检查超时时间
CHECK_TERMINAL_TIMEOUT = 20

# 链路
TUNNELS = ({
    'id': 'hk',
    'name': '香港',
    'ip': '159.138.4.156',
}, {
    'id': 'sg',
    'name': '新加坡',
    'ip': '47.74.229.135',
})

# 基础镜像
BASE_IMAGES = ({
    'dis_name': 'windows-10',
    'name': 'default-windows-10',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.WINDOWS,
    'system_sub_type': StandardDevice.SystemSubType.WINDOWS_10,
    'access_mode': 'rdp',
    'access_port': 3389,
    'security': 'nla',
    'user': 'Administrator',
    'password': 'password',
    'flavor': 'm3.1c-2g-20g',
    'init_support': True,
}, {
    'dis_name': 'windows-8',
    'name': 'default-windows-8',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.WINDOWS,
    'system_sub_type': StandardDevice.SystemSubType.WINDOWS_8,
    'access_mode': 'rdp',
    'access_port': 3389,
    'security': 'nla',
    'user': 'root',
    'password': 'password',
    'flavor': 'm3.1c-2g-20g',
    'init_support': True,
}, {
    'dis_name': 'windows-7',
    'name': 'default-windows-7',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.WINDOWS,
    'system_sub_type': StandardDevice.SystemSubType.WINDOWS_7,
    'access_mode': 'rdp',
    'access_port': 3389,
    'security': 'nla',
    'user': 'Administrator',
    'password': 'password',
    'flavor': 'm3.1c-2g-20g',
    'init_support': True,
}, {
    'dis_name': 'windows-xp',
    'name': 'default-windows-xp',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.WINDOWS,
    'system_sub_type': StandardDevice.SystemSubType.WINDOWS_XP,
    'access_mode': 'rdp',
    'access_port': 3389,
    'security': 'rdp',
    'user': 'Administrator',
    'password': 'password',
    'flavor': 'm2.1c-1g-10g',
    'init_support': True,
}, {
    'dis_name': 'windows-server-2012',
    'name': 'default-windows-server-2012',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.WINDOWS,
    'system_sub_type': StandardDevice.SystemSubType.WINDOWS_SERVER_2012,
    'access_mode': 'rdp',
    'access_port': 3389,
    'security': 'nla',
    'user': 'Administrator',
    'password': 'password_win2012',
    'flavor': 'm3.1c-2g-20g',
    'init_support': True,
}, {
    'dis_name': 'windows-server-2008',
    'name': 'default-windows-server-2008',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.WINDOWS,
    'system_sub_type': StandardDevice.SystemSubType.WINDOWS_SERVER_2008,
    'access_mode': 'rdp',
    'access_port': 3389,
    'security': 'nla',
    'user': 'Administrator',
    'password': 'password_win2008',
    'flavor': 'm3.1c-2g-20g',
    'init_support': True,
}, {
    'dis_name': 'windows-server-2003',
    'name': 'default-windows-server-2003',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.WINDOWS,
    'system_sub_type': StandardDevice.SystemSubType.WINDOWS_SERVER_2003,
    'access_mode': 'rdp',
    'access_port': 3389,
    'security': 'rdp',
    'user': 'Administrator',
    'password': 'password',
    'flavor': 'm2.1c-1g-10g',
    'init_support': True,
}, {
    'dis_name': 'windows-server-2000',
    'name': 'default-windows-server-2000',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.WINDOWS,
    'system_sub_type': StandardDevice.SystemSubType.WINDOWS_SERVER_2000,
    'access_mode': 'rdp',
    'access_port': 3389,
    'security': 'rdp',
    'user': 'Administrator',
    'password': 'password',
    'flavor': 'm2.1c-1g-10g',
    'init_support': False,
}, {
    'dis_name': 'ubuntu-16',
    'name': 'default-ubuntu-16',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.LINUX,
    'system_sub_type': StandardDevice.SystemSubType.UBUNTU_16,
    'access_mode': 'ssh',
    'access_port': 22,
    'user': 'root',
    'password': 'password',
    'flavor': 'm2.1c-1g-10g',
    'init_support': True,
}, {
    'dis_name': 'centos-7',
    'name': 'default-centos-7',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.LINUX,
    'system_sub_type': StandardDevice.SystemSubType.CENTOS_7,
    'access_mode': 'ssh',
    'access_port': 22,
    'user': 'root',
    'password': 'password',
    'flavor': 'm2.1c-1g-10g',
    'init_support': True,
}, {
    'dis_name': 'kali-linux',
    'name': 'default-kali-linux',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.LINUX,
    'system_sub_type': StandardDevice.SystemSubType.KALI_2,
    'access_mode': 'ssh',
    'access_port': 22,
    'user': 'root',
    'password': 'password',
    'flavor': 'm3.1c-2g-20g',
    'init_support': False,
}, {
    'dis_name': 'android',
    'name': 'default-android',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.LINUX,
    'system_sub_type': StandardDevice.SystemSubType.ANDROID,
    'access_mode': 'console',
    'access_port': '',
    'user': '',
    'password': '',
    'flavor': 'm2.1c-1g-10g',
    'init_support': False,
    # }, {
    #     'dis_name': 'UbuntuKylin-18.04',
    #     'name': 'default-UbuntuKylin-18.04',
    #     'image_type': StandardDevice.ImageType.VM,
    #     'system_type': StandardDevice.SystemType.LINUX,
    #     'system_sub_type': StandardDevice.SystemSubType.UBUNTUKYLIN_18,
    #     'access_mode': 'rdp',
    #     'access_port': 3389,
    #     'security': 'rdp',
    #     'user': 'ubuntukylin',
    #     'password': 'kylin123',
    #     'flavor': 'm2.1c-1g-10g',
    #     'init_support': True,
    # }, {
    #     'dis_name': 'OpenSolaris-11',
    #     'name': 'default-OpenSolaris-11',
    #     'image_type': StandardDevice.ImageType.VM,
    #     'system_type': StandardDevice.SystemType.LINUX,
    #     'system_sub_type': StandardDevice.SystemSubType.OPENSOLARIS_11,
    #     'access_mode': 'ssh',
    #     'access_port': 22,
    #     'user': 'root',
    #     'password': 'root123',
    #     'flavor': 'm3.1c-1g-20g',
    #     'init_support': False,
    # }, {
    #     'dis_name': 'OpenSUSE-Leap-42.3',
    #     'name': 'default-OpenSUSE-Leap-42.3',
    #     'image_type': StandardDevice.ImageType.VM,
    #     'system_type': StandardDevice.SystemType.LINUX,
    #     'system_sub_type': StandardDevice.SystemSubType.OPENSUSE_LEAP_42,
    #     'access_mode': 'ssh',
    #     'access_port': 22,
    #     'user': 'root',
    #     'password': 'root',
    #     'flavor': 'm2.1c-1g-10g',
    #     'init_support': True,
    # }, {
    #     'dis_name': 'debian-9.5',
    #     'name': 'default-debian-9.5.0',
    #     'image_type': StandardDevice.ImageType.VM,
    #     'system_type': StandardDevice.SystemType.LINUX,
    #     'system_sub_type': StandardDevice.SystemSubType.DEBIAN_9,
    #     'access_mode': 'ssh',
    #     'access_port': 22,
    #     'user': 'debian',
    #     'password': 'debian',
    #     'flavor': 'm2.1c-1g-10g',
    #     'init_support': True,
}, {
    'dis_name': 'deepofix',
    'name': 'default-deepofix',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.LINUX,
    'system_sub_type': StandardDevice.SystemSubType.DEEPOFIX,
    'access_mode': 'ssh',
    'access_port': 22,
    'user': 'root',
    'password': 'root',
    'flavor': 'm2.1c-1g-10g',
    'init_support': False,
}, {
    'dis_name': 'redhat-7',
    'name': 'default-redhat-7',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.LINUX,
    'system_sub_type': StandardDevice.SystemSubType.REDHAT_7,
    'access_mode': 'ssh',
    'access_port': 22,
    'user': 'root',
    'password': 'password',
    'flavor': 'm2.1c-1g-10g',
    'init_support': True,
}, {
    'dis_name': 'backtrack-5',
    'name': 'default-backtrack-5',
    'image_type': StandardDevice.ImageType.VM,
    'system_type': StandardDevice.SystemType.LINUX,
    'system_sub_type': StandardDevice.SystemSubType.BACKTRACK_5,
    'access_mode': 'console',
    'access_port': '',
    'user': 'root',
    'password': 'toor',
    'flavor': 'm2.1c-1g-10g',
    'init_support': False,
})


FLAVOR_INFO = [
    (StandardDevice.Flavor.M11C_05G_8G, _('x_m1.1c-0.5g-8g')),
    (StandardDevice.Flavor.M11C_1G_8G, _('x_m1.1c-1g-8g')),
    (StandardDevice.Flavor.M21C_05G_10G, _('x_m2.1c-0.5g-10g')),
    (StandardDevice.Flavor.M21C_1G_10G, _('x_m2.1c-1g-10g')),
    (StandardDevice.Flavor.M22C_2G_10G, _('x_m2.2c-2g-10g')),
    (StandardDevice.Flavor.M22C_4G_10G, _('x_m2.2c-4g-10g')),
    (StandardDevice.Flavor.M31C_1G_20G, _('x_m3.1c-1g-20g')),
    (StandardDevice.Flavor.M31C_2G_20G, _('x_m3.1c-2g-20g')),
    (StandardDevice.Flavor.M32C_4G_20G, _('x_m3.2c-4g-20g')),
    (StandardDevice.Flavor.M34C_4G_20G, _('x_m3.4c-4g-20g')),
    (StandardDevice.Flavor.M41C_1G_40G, _('x_m4.1c-1g-40g')),
    (StandardDevice.Flavor.M42C_2G_40G, _('x_m4.2c-2g-40g')),
    (StandardDevice.Flavor.M44C_4G_40G, _('x_m4.4c-4g-40g')),
    (StandardDevice.Flavor.M44C_8G_40G, _('x_m4.4c-8g-40g')),
    (StandardDevice.Flavor.M54C_4G_80G, _('x_m5.4c-4g-80g')),
    (StandardDevice.Flavor.M54C_8G_80G, _('x_m5.4c-8g-80g')),
]


def load_related(app_settings):
    app_settings.FULL_DEFAULT_DEVICE_LOGO_DIR = os.path.join(settings.MEDIA_ROOT, app_settings.DEFAULT_DEVICE_LOGO_DIR)
    app_settings.BASE_IMAGE_NAMES = [image['name'] for image in BASE_IMAGES]
    app_settings.BASE_IMAGE_MAPPING = {image['name']: image for image in BASE_IMAGES}
