# -*- coding: utf-8 -*-
import json

from django.db import models
from django.utils import timezone

from base.models import Executor
from base.utils.enum import Enum
from base.utils.models.manager import MManager

from base_auth.models import User, Owner
from base_cloud import api as cloud


class SceneConfig(Owner):
    Type = Enum(
        BASE=1,
    )
    type = models.PositiveIntegerField(default=Type.BASE)
    file = models.FileField(upload_to='scene', null=True, default=None)
    json_config = models.TextField(default='{}')

    # info from json
    name = models.CharField(max_length=100, default=None, null=True)


class Scene(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, default=None, null=True)
    Type = SceneConfig.Type
    type = models.PositiveIntegerField(default=Type.BASE)
    file = models.FileField(upload_to='scene', null=True, default=None)
    json_config = models.TextField(default='{}')

    # 被外部引用的关系
    hang_info = models.TextField(default='{}')
    # 资源名称前缀
    name_prefix = models.CharField(max_length=100, default='')
    Status = Enum(
        DELETED=0,
        CREATING=1,
        RUNNING=2,
        PAUSE=3,
        ERROR=4,
    )
    status = models.IntegerField(default=Status.CREATING)
    status_updated = models.ForeignKey(Executor, on_delete=models.SET_NULL, default=None, null=True, related_name='+')
    # 记录环境创建流程日志
    log = models.TextField(default='[]')
    # 记录环境出错信息
    error = models.CharField(max_length=2048, default=None, null=True)

    # 环境创建时间
    create_time = models.DateTimeField(default=timezone.now)
    # 环境创建完成时间
    created_time = models.DateTimeField(default=None, null=True)
    # 环境创建消耗时间
    consume_time = models.PositiveIntegerField(default=0)
    # 环境暂停时间
    pause_time = models.DateTimeField(default=None, null=True)

    @property
    def name(self):
        return json.loads(self.json_config).get('scene', {}).get('name')


# 标靶
class StandardDevice(Owner):
    name = models.CharField(max_length=100)
    description = models.TextField(default='')
    logo = models.ImageField(upload_to='standard_device_logo', null=True)
    # 设备角色：网关，网络，终端
    Role = Enum(
        NETWORK=1,
        GATEWAY=2,
        TERMINAL=3,
    )
    role = models.PositiveIntegerField()
    RoleNetworkType = Enum(
        NETWORK=1,
    )
    RoleGatewayType = Enum(
        ROUTER=1,
        FIREWALL=2,
        TERMINAL_ROUTER=3,
        TERMINAL_FIREWALL=4,
        WAF=5,
        IPS=6,
        IDS=7,
    )
    RoleTerminalType = Enum(
        OTHER=0,
        WEB_SERVER=1,
        DATABASE_SERVER=2,
        FILE_SERVER=3,
        BINARY_SERVER=4,
        MAIL_SERVER=5,
        OFFICE_EQUIPMENT=6,
        MOBILE_EQUIPMENT=7,
        INDUSTRIAL_CONTROL_EQUIPMENT=8,
        INTELLIGENT_EQUIPMENT=9,
        UAV=10,

        REMOTE_ADDRESS_SERVER=-1,
        DEVICE_PORT_SERVER=-2,
        WIRELESS_SERVER=-3,
    )
    RoleType = {
        Role.NETWORK: RoleNetworkType,
        Role.GATEWAY: RoleGatewayType,
        Role.TERMINAL: RoleTerminalType,
    }
    role_type = models.IntegerField()
    is_real = models.BooleanField(default=False)

    # -- 路由属性 --
    GatewayPortType = Enum(
        MANAGE=0,
        WAN=1,
        LAN=2,
    )
    gateway_port_configs = models.TextField(default='[]')

    # -- 终端属性 --
    # 镜像类型
    ImageType = Enum(
        VM='vm',
        DOCKER='docker',
        REAL='real',
    )
    image_type = models.CharField(max_length=100, null=True, default=None)
    # 系统类型
    SystemType = Enum(
        LINUX='linux',
        WINDOWS='windows',
        OTHER='other',
    )
    system_type = models.CharField(max_length=100, null=True, default=SystemType.OTHER)
    # 系统二级类型
    SystemSubType = Enum(
        KALI_2='kali-2',
        UBUNTU_14='ubuntu-14',
        UBUNTU_16='ubuntu-16',
        CENTOS_7='centos-7',
        WINDOWS_XP='windows-xp',
        WINDOWS_7='windows-7',
        WINDOWS_8='windows-8',
        WINDOWS_10='windows-10',
        WINDOWS_SERVER_2012='windows-server-2012',
        WINDOWS_SERVER_2008='windows-server-2008',
        WINDOWS_SERVER_2003='windows-server-2003',
        WINDOWS_SERVER_2000='windows-server-2000',
        ANDROID='android',
        UBUNTUKYLIN_18='ubuntukylin-18',
        OPENSOLARIS_11='opensolaris-11',
        OPENSUSE_LEAP_42='opensuse-leap-42',
        DEBIAN_9='debian-9',
        DEEPOFIX='deepofix',
        REDHAT_7='redhat-7',
        BACKTRACK_5='backtrack-5',
        OTHER='other',
    )
    SystemSubTypeMap = {
        SystemSubType.KALI_2: SystemType.LINUX,
        SystemSubType.UBUNTU_14: SystemType.LINUX,
        SystemSubType.UBUNTU_16: SystemType.LINUX,
        SystemSubType.CENTOS_7: SystemType.LINUX,
        SystemSubType.WINDOWS_XP: SystemType.WINDOWS,
        SystemSubType.WINDOWS_7: SystemType.WINDOWS,
        SystemSubType.WINDOWS_8: SystemType.WINDOWS,
        SystemSubType.WINDOWS_10: SystemType.WINDOWS,
        SystemSubType.WINDOWS_SERVER_2012: SystemType.WINDOWS,
        SystemSubType.WINDOWS_SERVER_2008: SystemType.WINDOWS,
        SystemSubType.WINDOWS_SERVER_2003: SystemType.WINDOWS,
        SystemSubType.WINDOWS_SERVER_2000: SystemType.WINDOWS,
        SystemSubType.ANDROID: SystemType.LINUX,
        SystemSubType.UBUNTUKYLIN_18: SystemType.LINUX,
        SystemSubType.OPENSOLARIS_11: SystemType.LINUX,
        SystemSubType.OPENSUSE_LEAP_42: SystemType.LINUX,
        SystemSubType.DEBIAN_9: SystemType.LINUX,
        SystemSubType.DEEPOFIX: SystemType.LINUX,
        SystemSubType.REDHAT_7: SystemType.LINUX,
        SystemSubType.BACKTRACK_5: SystemType.LINUX,
        SystemSubType.OTHER: SystemType.OTHER,
    }
    system_sub_type = models.CharField(max_length=100, null=True, default=SystemSubType.OTHER)
    # 来源基础镜像
    source_image_name = models.CharField(max_length=100, null=True, default=None)
    # 镜像格式(上传)
    DiskFormat = Enum(
        QCOW2='qcow2',
        VMDK='vmdk',
        DOCKER='docker',
        VHD='vhd',
        VDI='vdi',
        AMI='ami',
        ARI='ari',
        ISO='iso',
        OVA='ova',
        RAW='raw',
    )
    disk_format = models.CharField(max_length=100, null=True, default=None)
    # 镜像元数据
    DiskController = Enum(
        NONE='',
        IDE='ide',
        VIRTIO='virtio',
        SCSI='scsi',
        UML='uml',
        XEN='xen',
        USB='usb',
    )
    VirtualNetworkInterfaceDevice = Enum(
        NONE='',
        RTL8139='rtl8139',
        VIRTIO='virtio',
        E1000='e1000',
        NE2K_PCI='ne2k_pci',
        PCNET='pcnet',
    )
    VideoImageDriver = Enum(
        NONE='',
        VGA='vga',
        CIRRUS='cirrus',
        VMVGA='vmvga',
        XEN='xen',
        QXL='qxl',
    )
    meta_data = models.TextField(null=True, default=None)
    # 镜像大小 对应EnvTerminal.Flavor
    Flavor = Enum(
        M11C_05G_8G='m1.1c-0.5g-8g',
        M11C_1G_8G='m1.1c-1g-8g',
        M21C_05G_10G='m2.1c-0.5g-10g',
        M21C_1G_10G='m2.1c-1g-10g',
        M22C_2G_10G='m2.2c-2g-10g',
        M22C_4G_10G='m2.2c-4g-10g',
        M31C_1G_20G='m3.1c-1g-20g',
        M31C_2G_20G='m3.1c-2g-20g',
        M32C_4G_20G='m3.2c-4g-20g',
        M34C_4G_20G='m3.4c-4g-20g',
        M41C_1G_40G='m4.1c-1g-40g',
        M42C_2G_40G='m4.2c-2g-40g',
        M44C_4G_40G='m4.4c-4g-40g',
        M44C_8G_40G='m4.4c-8g-40g',
        M54C_4G_80G='m5.4c-4g-80g',
        M54C_8G_80G='m5.4c-8g-80g',
    )
    flavor = models.CharField(max_length=100, null=True, default=None)
    # 默认访问方式 对应EnvTerminal.AccessMode
    access_mode = models.CharField(max_length=100, null=True, default=None)
    # 默认访问端口
    access_port = models.CharField(max_length=32, default=None, null=True)
    # 默认连接模式 目前只针对rdp的guacamole连接的rdp/nla
    access_connection_mode = models.CharField(max_length=100, null=True, default=None)
    # 默认访问用户 对应EnvTerminal.AccessMode
    access_user = models.CharField(max_length=100, null=True, default=None)
    # 默认访问密码 对应EnvTerminal.AccessMode
    access_password = models.CharField(max_length=256, null=True, default=None)
    # 是否支持初始化
    init_support = models.BooleanField(default=False)
    # 镜像状态
    ImageStatus = Enum(
        NOT_APPLY=0,
        CREATING=1,
        CREATED=2,
        ERROR=3,
    )
    image_status = models.PositiveIntegerField(default=ImageStatus.NOT_APPLY)
    image_status_updated = models.ForeignKey(Executor, on_delete=models.SET_NULL, default=None, null=True,
                                             related_name='+')
    error = models.CharField(max_length=2048, default=None, null=True)
    # 临时编辑的镜像场景
    image_scene = models.ForeignKey(Scene, on_delete=models.SET_NULL, null=True, default=None)

    # type
    Type = Enum(
        NORMAL=0,
        TRM=1,
        TGM=2,
        CGM=3,
    )
    type = models.PositiveIntegerField(default=Type.NORMAL)

    # 实体设备
    port_map = models.TextField(default='[]')
    remote_address = models.CharField(max_length=128, null=True, default="")

    Status = Enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.IntegerField(default=Status.NORMAL)

    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()


class StandardDeviceSnapshot(models.Model):
    standard_device = models.ForeignKey(StandardDevice)
    name = models.CharField(max_length=128)
    desc = models.CharField(max_length=1024)
    create_time = models.DateTimeField(default=timezone.now)


class SceneNode(models.Model):
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE, default=None, null=True)
    sub_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100, default=None, null=True)
    is_real = models.BooleanField(default=False)
    visible = models.BooleanField(default=True)

    class Meta:
        abstract = True
        unique_together = ('scene', 'sub_id')


class SceneNet(SceneNode):
    Type = StandardDevice.RoleNetworkType
    type = models.PositiveIntegerField(default=Type.NETWORK)
    image = models.CharField(max_length=100, default='')
    cidr = models.CharField(max_length=1024, default=None, null=True)
    gateway = models.CharField(max_length=1024, default=None, null=True)
    dns = models.CharField(max_length=1024, default=None, null=True)
    dhcp = models.BooleanField(default=True)

    net_id = models.CharField(max_length=50, default=None, null=True)
    subnet_id = models.CharField(max_length=50, default=None, null=True)
    vlan_id = models.CharField(max_length=50, default=None, null=True)
    vlan_info = models.TextField(default='')
    # 本地代理路由
    proxy_router_id = models.CharField(max_length=50, default=None, null=True)


class SceneGateway(SceneNode):
    Type = StandardDevice.RoleGatewayType
    type = models.PositiveIntegerField(default=Type.ROUTER)
    image = models.CharField(max_length=100, default='')
    nets = models.ManyToManyField(SceneNet)
    net_configs = models.TextField(default='[]')

    # 路由器/防火墙属性
    router_id = models.CharField(max_length=50, default=None, null=True)
    static_routing = models.TextField(default='')
    # 防火墙属性
    firewall_rule = models.TextField(default='')
    firewall_id = models.CharField(max_length=50, default=None, null=True)
    can_user_configure = models.BooleanField(default=False)


class SceneTerminal(SceneNode):
    Type = StandardDevice.RoleTerminalType
    type = models.PositiveIntegerField(default=Type.OTHER)
    nets = models.ManyToManyField(SceneNet)

    # 服务器属性
    SystemType = StandardDevice.SystemType
    system_type = models.CharField(max_length=100, default=SystemType.LINUX)
    SystemSubType = StandardDevice.SystemSubType
    system_sub_type = models.CharField(max_length=100, default=SystemSubType.OTHER)
    ImageType = StandardDevice.ImageType
    image_type = models.CharField(max_length=100, default=ImageType.VM)
    image = models.CharField(max_length=100)
    Role = Enum(
        OPERATOR='operator',
        TARGET='target',
        WINGMAN='wingman',
        GATEWAY='gateway',
        EXECUTER='executer',
    )
    role = models.CharField(max_length=100, default=Role.TARGET)
    Flavor = StandardDevice.Flavor
    flavor = models.CharField(max_length=100, default=None, null=True)
    custom_script = models.CharField(max_length=2048, default=None, null=True)
    init_script = models.CharField(max_length=2048, default=None, null=True)
    install_script = models.CharField(max_length=2048, default=None, null=True)
    deploy_script = models.CharField(max_length=2048, default=None, null=True)
    clean_script = models.CharField(max_length=2048, default=None, null=True)
    push_flag_script = models.CharField(max_length=2048, default=None, null=True)
    check_script = models.CharField(max_length=2048, default=None, null=True)
    attack_script = models.CharField(max_length=2048, default=None, null=True)
    checker = models.CharField(max_length=100, default=None, null=True)
    attacker = models.CharField(max_length=100, default=None, null=True)
    external = models.BooleanField(default=False)
    net_configs = models.TextField(default='[]')
    AccessBaseProtocol = Enum(
        TCP='tcp',
        UDP='udp',
    )
    AccessMode = Enum(
        HTTP='http',
        HTTPS='https',
        NC='nc',
        SSH='ssh',
        RDP='rdp',
        CONSOLE='console',
        TELNET='telnet'
    )
    AccessModeDefaultPort = {
        AccessMode.HTTP: 80,
        AccessMode.HTTPS: 443,
        AccessMode.NC: 9999,
        AccessMode.SSH: 22,
        AccessMode.RDP: 3389,
        AccessMode.TELNET: 23,
    }
    raw_access_modes = models.TextField(default='[]')
    access_modes = models.TextField(default='[]')
    installers = models.TextField(default='[]')
    tunnel = models.CharField(max_length=100, default='')

    Status = Enum(
        PREPARING=-2,
        PREPARED=-1,
        DELETED=0,
        CREATING=1,
        HATCHING=2,
        STARTING=3,
        DEPLOYING=4,
        RUNNING=5,
        PAUSE=6,
        ERROR=7,
    )
    status = models.IntegerField(default=Status.CREATING)
    error = models.CharField(max_length=2048, default=None, null=True)

    server_id = models.CharField(max_length=50, default=None, null=True)
    volumes = models.TextField(default='[]')
    policies = models.TextField(default='[]')
    net_ports = models.TextField(default='[]')
    # 平台可直接访问的ip(直连外网ip或浮动ip)
    float_ip = models.CharField(max_length=32, default=None, null=True)
    # 宿主机ip
    host_ip = models.CharField(max_length=32, default=None, null=True)
    host_name = models.CharField(max_length=1024, default=None, null=True)
    # 宿主机代理 {"http:80": {"id": "123456", "port": 12309}, "ssh:22": {"id": "123457", "port": 23543}}
    host_proxy_port = models.TextField(default='{}')
    # 平台代理 {"http:80": 12309, "ssh:22": 23543}
    proxy_port = models.TextField(default='{}')

    # 机器创建时间
    create_time = models.DateTimeField(default=timezone.now)
    # 机器创建完成时间
    created_time = models.DateTimeField(default=None, null=True)
    # 机器创建消耗时间
    consume_time = models.PositiveIntegerField(default=0)
    # 机器暂停时间
    pause_time = models.DateTimeField(default=None, null=True)

    # 创建server参数用于重建
    create_params = models.TextField(default='{}')
    # 浮动ip参数用于重建
    float_ip_params = models.TextField(default='{}')
    # 自定义字段
    extra = models.TextField(default='')


class InstallerType(models.Model):
    name = models.CharField(max_length=100)


class InstallerResource(models.Model):
    Platform = StandardDevice.SystemSubType
    platforms = models.CharField(max_length=1024, default='', blank=True)
    name = models.CharField(max_length=1024, default='', blank=True)
    file = models.FileField(upload_to='installer', null=True, default=None)
    encrypt_file = models.FileField(upload_to='encrypt_installer', null=True, default=None)
    encrypt_password = models.CharField(max_length=1024, default='', blank=True)
    install_script = models.CharField(max_length=2048, default='', blank=True)


# 安装程序
class Installer(Owner):
    name = models.CharField(max_length=100)
    type = models.ForeignKey(InstallerType, on_delete=models.PROTECT)

    resources = models.ManyToManyField(InstallerResource)
    Status = Enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.IntegerField(default=Status.NORMAL)

    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()


# 云盘
class Disk(Owner):
    name = models.CharField(max_length=100, unique=True)
    size = models.PositiveIntegerField()
    used_size = models.FloatField(default=0)
    Format = Enum(
        NTFS='NTFS',
        EXT4='EXT4',
        FAT32='FAT32',
    )
    format = models.CharField(max_length=100, default=Format.NTFS)
    disk_id = models.CharField(max_length=50, default=None, null=True)
    mnt_dir = models.CharField(max_length=1024, default=None, null=True)
    Status = Enum(
        DELETE=0,
        AVAILABLE=1,
        USING=2,
        DETACHING=3,
        ERROR=4,
    )
    status = models.IntegerField(default=Status.AVAILABLE)

    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()

    def sync(self):
        if self.status != Disk.Status.DELETE and self.disk_id:
            status_map = {
                'available': Disk.Status.AVAILABLE,
                'in-use': Disk.Status.USING,
                'detaching': Disk.Status.DETACHING,
                'error': Disk.Status.ERROR,
            }
            disk = cloud.volume.get(self.disk_id)
            self.name = disk.name
            self.size = disk.size
            self.modify_time = timezone.now()
            self.status = status_map.get(disk.status, Disk.Status.AVAILABLE)
            self.save()


# 网络
class Network(Owner):
    name = models.CharField(max_length=100, unique=True)
    company = models.CharField(max_length=100, default=None, null=True)
    cidr = models.CharField(max_length=1024, default=None, null=True)
    gateway = models.CharField(max_length=1024, default=None, null=True)
    dns = models.CharField(max_length=1024, default=None, null=True)
    dhcp = models.BooleanField(default=True)
    net_id = models.CharField(max_length=50, default=None, null=True)
    subnet_id = models.CharField(max_length=50, default=None, null=True)
    Status = Enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.IntegerField(default=Status.NORMAL)
    objects = MManager({'status': Status.DELETE})
    original_objects = models.Manager()
