#!/usr/bin/env python
# encoding: utf-8
# @author: wangheng
# @contact: wangh@cyberpeace.cn
# @software: PyCharm
# @file: topo_generator.py
# @time: 18-7-14 12:24

import json
import random
import copy
import logging
from sisdk.libcr.enums import EnumDeviceType, EnumEntityType
from .cr_topology_pb2 import topology_net_entity

BACK_GROUND_COLORS = "red,cyan,blue,darkblue,lightblue,purple,yellow,lime,fuchsia,white,silver,grey,black,orange,brown,maroon,green,olive,navy,teal,aqua,magenta".split(",")

class Orientation(object):
    automatic = 0
    horizontal = 1      #横向
    vertical = 2        #纵向

class DuplicateIdException(BaseException):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class NetEntity(object):
    #net_ids = []

    def __init__(self, entity_id="", entity_name=""):
        # if entity_name in NetEntity.net_ids:
        #     raise DuplicateIdException("Duplicate Id in net_entity.")
        self.id = entity_id
        #NetEntity.net_ids.append(entity_name)
        self.name = entity_name         #名字
        self.device_type = EnumDeviceType.empty          #设备类型：abstract表示不是个实物设备，其它在基类定义
        self.entity_type = EnumEntityType.abstract       #实体类型：有subnet, net_device, net_host，后面可换为枚举
        self.parent_id = "-1"             #父节点ID，暂时没用到
        self.linebreak_count = 5           #排多少个节点后换行（用于自动生成时排）
        self.parent = None
        self.backgroud_color = random.choice(BACK_GROUND_COLORS)    #背景色,空为透明
        self.label = ""                 #标签，暂时没用到
        self.logo = ""                  #LOGO，暂时没用到
        self.width = 0                  #实体的宽度，暂时没用到
        self.height = 0                 #实体的高度，暂时没用到
        self.units_gap = 0                #两个实体间的空位
        self.primary = None             #主结点
        self.is_primary = False         #是否为主结点
        self.children = []              #子结点列表
        self.switch_arrange = False     #设置为True时到此节点会换行
        self.merge_subline = False      #是否合并子节点的网线
        self.orientation = Orientation.horizontal #子结点排布方式（这块可以扩展出很多种）

    @staticmethod
    def initialize():
        NetEntity.net_ids = []

    def set_primary(self, entity):
        entity.is_primary = True
        self.primary = entity

    def get_entity_ids(self,entity_type, device_type=None):
        ids = []
        if self.entity_type == entity_type:
            ids.append(self.id)
        if self.primary:
            if self.primary.entity_type == entity_type:
                ids.append(self.primary.id)
        if self.children:
            for child in self.children:
                child_ids = child.get_entity_ids(entity_type)
                ids.extend(child_ids)
        return ids

    def to_binary(self):
        if self.primary:
            primary_data = self.primary.to_binary()
        else:
            primary_data = None
        proto_data = topology_net_entity(id=self.id,
                                         name=self.name,
                                         parent_id=self.parent_id,
                                         is_primary=self.is_primary,
                                         primary=primary_data,
                                         entity_type=self.entity_type,
                                         device_type=self.device_type,
                                         orientation=self.orientation,
                                         background_color=self.backgroud_color,
                                         switch_arrange=self.switch_arrange,
                                         units_gap=self.units_gap,
                                         merge_subline=self.merge_subline)
        if len(self.children) > 0:
            this_children = []
            for child in self.children:
                this_children.append(child.to_binary())
            proto_data.children.extend(this_children)
        return proto_data


    def from_json(self, str_json):
        """
        从一段json载入数据
        :param str_json: json字符串
        """
        data = json.loads(str_json)
        self.from_dict(data)

    def from_dict(self, data):
        """
        从一个字典载入数据
        :param data: 字典数据
        """
        self.id = data["id"]
        self.name = data["name"]
        self.is_primary = data["is_primary"]
        if data["primary"]:
            primary_node = NetEntity()
            primary_node.from_dict(data["primary"])
            self.primary = primary_node
        else:
            self.primary = None
        self.device_type = data["device_type"]
        self.entity_type = data["entity_type"]
        self.parent_id = data["parent_id"]
        self.width = data["width"]
        self.height = data["height"]
        self.backgroud_color = data["background_color"]
        self.units_gap = data["units_gap"]
        self.switch_arrange = data["switch_arrange"]
        if len(data["children"]) > 0:
            children = []
            for child_data in data["children"]:
                child_obj = NetEntity()
                child_obj.from_dict(child_data)
                child_obj.parent = self
                children.append(child_obj)
            self.children = children
        else:
            self.children = []

    def to_dict(self):
        """
        序列化为字典
        """
        dict_data = {"id": self.id,
                     "name": self.name,
                     "parent_id": self.parent_id,
                     "is_primary": self.is_primary,
                     "primary": self.primary.to_dict() if self.primary else "",
                     "device_type": self.device_type,
                     "entity_type": self.entity_type,
                     "width": self.width,
                     "height": self.height,
                     "orientation": self.orientation,
                     "background_color": self.backgroud_color,
                     "switch_arrange": self.switch_arrange,
                     "units_gap": self.units_gap,
                     "children": [child.to_dict() for child in self.children]}
        return dict_data

    def to_json(self):
        """
        序列化为json字符串
        """
        return json.dumps(self.to_dict())

    def __repr__(self):
        return "<%s object at %d>" % (self.name,id(self))

class Subnet(NetEntity):
    """
    子网类
    """
    def __init__(self, entity_id, entity_name, linebreak=5, background="", merge_subline=False):
        super(Subnet, self).__init__(entity_id, entity_name)
        self.entity_type = EnumEntityType.subnet
        self.linebreak_count = linebreak
        self.merge_subline = merge_subline
        if background:
            self.backgroud_color = background

    def add_child(self, obj_entity):
        if len(self.children) > 0 and (len(self.children) % self.linebreak_count == 0):
            switch_arrange = True
        else:
            switch_arrange = False
        if isinstance(obj_entity, list):
            for obj in obj_entity:
                obj.switch_arrange = switch_arrange
            self.children.extend(obj_entity)
        else:
            obj_entity.switch_arrange = switch_arrange
            self.children.append(obj_entity)

    def gen_children(self, net_ip, device_type, host_count):
        for i in range(1, host_count + 1):
            host_ip = net_ip + str(i)
            host = NetDevice(host_ip, device_type)
            if i % self.linebreak_count == 0:
                host.switch_arrange = True
            self.children.append(host)

class NetDevice(NetEntity):
    """
    网络设备和主机类
    """
    def __init__(self, entity_id, entity_name, dev_type=EnumDeviceType.server):
        super(NetDevice, self).__init__(entity_id, entity_name)
        self.entity_type = EnumEntityType.device
        self.device_type = dev_type
        self.width = 50
        self.height = 50
        self.backgroud_color = ""

class XojScene(object):
    """
    完成xoj场景描述文件到拓扑数据的生成
    """
    def __init__(self):
        self.entities = []
        self.gateways = []
        self.networks = []
        self.servers = []
        self.travelled = []

    def get_entity(self, id_or_name):
        for obj in self.entities:
            if obj.name == id_or_name:
                return copy.deepcopy(obj)
            if obj.id == id_or_name:
                return copy.deepcopy(obj)

    def from_json(self, json_str):
        """
        从xoj的场景描述文件中生成拓扑结构
        :param json_str:  xoj的场景描述数据
        """
        oj_data = json.loads(json_str)
        firewalls = oj_data.get("firewalls", [])
        routers = oj_data.get("routers", [])
        networks = oj_data.get("networks", [])
        servers = oj_data.get("servers",[])
        self.root_entity = None

        # 添加firewall对象
        for fw in firewalls:
            obj_fw = Subnet(fw['id'],fw['name'],2,"black")
            primary = NetDevice(fw['id'] + "_prim", fw['id'] + "_prim", EnumDeviceType.firewall)
            primary.is_primary = True
            obj_fw.primary = primary
            obj_fw.networks = fw['net']
            self.gateways.append(obj_fw)
            self.entities.append(obj_fw)
        # 添加router对象
        for rt in routers:
            obj_rt = Subnet(rt['id'], rt['name'], 2, "black")
            primary = NetDevice(rt['id'] + "_prim", rt['id'] + "_prim", EnumDeviceType.router)
            primary.is_primary = True
            obj_rt.primary = primary
            obj_rt.networks = rt['net']
            self.gateways.append(obj_rt)
            self.entities.append(obj_rt)
        # 添加network对象
        for nw in networks:
            obj_nw = Subnet(nw['id'], nw['name'], 5, "black")
            primary = NetDevice(nw['id'] + "_prim", nw['id'] + "_prim", EnumDeviceType.switch)
            primary.is_primary = True
            obj_nw.primary = primary
            obj_nw.networks = []
            self.networks.append(obj_nw)
            self.entities.append(obj_nw)
        # 添加server对象
        for sv in servers:
            obj_sv = NetDevice(sv['id'], sv['name'], EnumDeviceType.server)
            # 有时候net对象是一个字典
            if isinstance(sv['net'][0], dict):
                obj_sv.network = sv['net'][0]['id']
            else:
                obj_sv.network = sv['net'][0]
            self.servers.append(obj_sv)
        # 将server组织到network里
        for nw in self.networks:
            for sv in self.servers:
                if sv.network == nw.id:
                    nw.add_child(sv)
        logging.debug("Scene loaded.")

    def make_tree(self, root_id_or_name, auto_arrange_root=True):
        """
        指定一个根节点，把网络数据生成一个树型结构
        :param root_id_or_name:  根节点的id或name，如果指定name可能会有岐义
        :param auto_arrange_root:  是否自动圆周排布根节点的子节点
        :return: 生成后会设置self.root_entity属性，返回True表示成功，False表示失败
        """
        self.travelled = []
        self.root_entity = self.get_entity(root_id_or_name)
        # 如果自动编排根节点，那么按照圆周分布子节点
        if auto_arrange_root:
            root_orientation = Orientation.automatic
        else:
            root_orientation = Orientation.horizontal
        # 如果找到了根结节，再开始处理后续事情
        if self.root_entity:
            self.root_entity.orientation = root_orientation
            self.__recursive_make_tree(self.root_entity)
            # 检查一下所有的子节点有没有这两种情况：1、空的网絽，2、直接连接终端
            # 这两种情况分别添加一个占位的服务器和一个占位的网络
            for child in self.root_entity.children:
                if child.entity_type == EnumEntityType.device:
                    # add a dummy network
                    dummy_net = Subnet("Dummy", "", 5, "purple")
                    dummy_net_router = NetDevice("RT-Dummy", "RT-Dummy", EnumDeviceType.router)
                    dummy_net.set_primary(dummy_net_router)
                    dummy_net.add_child(child)
                    self.root_entity.children.remove(child)
                    self.root_entity.add_child(dummy_net)
                elif child.entity_type == EnumEntityType.subnet and len(child.children) == 0:
                    # add a dummy device
                    dummy_device = NetDevice("Dummy", "", EnumDeviceType.server)
                    child.add_child(dummy_device)
            return True
        return False

    def __recursive_make_tree(self, root):
        """
        递归的方式生成树型结构
        :param root: 当前的相对根节点
        :return: 处理后的当前根节点
        """
        logging.info("Processing entity root id %s %s" % (root.id , self.travelled))
        # 如果已遍历过不再处理
        if root.id in self.travelled:
            logging.info("  Already processed: %s" % root.id)
            return None
        self.travelled.append(root.id)
        # 找到这个节点的networks中所指定的所有网络并连接上（firewall\router类节点有此属性）
        for net_id in root.networks:
            if net_id not in self.travelled:
                obj = self.get_entity(net_id)
                root.add_child(obj)
                logging.info("Adding object %s " % obj.id)
                self.__recursive_make_tree(obj)
        # 去找所有的节点中的networks中有没有包含这个节点，如果有连接上
        for obj in self.entities:
            if root.id in obj.networks:
                if obj.id not in self.travelled:
                    root.add_child(obj)
                    logging.info("  Adding object %s" % obj.id)
                    self.__recursive_make_tree(obj)
        return root

    def to_protobuf(self):
        if self.root_entity:
            return self.root_entity

    def to_binary(self):
        if self.root_entity:
            return self.root_entity.to_binary()

    def to_json(self):
        if self.root_entity:
            return self.root_entity.to_json()

class MultiXojScene(object):
    def __init__(self, root_name=""):
        self.root = Subnet("GLOBAL_ROOT_NODE", root_name)
        self.root.orientation = Orientation.automatic

    def add_subnet(self, subnet_json, root_name):
        subnet = XojScene()
        subnet.from_json(subnet_json)
        subnet.make_tree(root_name, False)
        obj = subnet.to_protobuf()
        self.root.add_child(obj)

    def to_binary(self):
        return self.root.to_binary()

    def to_json(self):
        return self.root.to_json()

