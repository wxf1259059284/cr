#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 18-11-15 下午2:10
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : mapscene.py
# @Project : cpss
from sisdk.libmap.map_sysctrl_pb2 import map_mark
from sisdk.messages import SequenceMessageMaker
from enums import EnumModelType, EnumStatus, EnumLineType, EnumEdgeStatus, EnumOnoff
from map_behavior_pb2 import net_entity, edge, model_pos, dest_object


class ModelPos(object):
    def __init__(self, longitude, latitude, altitude):
        self.longitude = longitude
        self.latitude = latitude
        self.altitude = altitude

    def to_protobuf(self):
        obj_pos = model_pos(longitude=self.longitude,
                            latitude=self.latitude,
                            altitude=self.altitude
                            )
        return obj_pos


class ModelDestObject(object):
    def __init__(self, dest_type, dest_id):
        self.dest_type = dest_type
        self.dest_id = dest_id

    def to_protobuf(self):
        dest_obj = dest_object(
            type=self.dest_type,
            dest_id=self.dest_id
        )
        return dest_obj


class MapMark(object):
    def __init__(self, name, longitude, latitude, mark_type):
        """
        在地图上添加一个地理位置
        :param name: XX省/XX市/XX县
        :param longitude: 经度
        :param latitude: 纬度
        :param mark_type: 省/市/县 类型见EnumMapMark
        """
        self.mark_type = mark_type
        self.longitude = longitude
        self.latitude = latitude
        self.name = name

    def to_protobuf(self):
        obj_mark = map_mark(
                                mark_type=self.mark_type,
                                longitude=self.longitude,
                                latitude=self.latitude,
                                name=self.name)
        return obj_mark


class MapEntity(object):
    def __init__(self, entity_id, entity_name,
                 model_type,
                 longitude,
                 latitude,
                 altitude=0,
                 model_color="red",
                 has_subnets=False,
                 parent_id="",
                 entity_switch=EnumOnoff.on):
        """
        在地图上添加一个实体
        :param entity_id: 实体的id
        :param entity_name: 实体的名字
        :param model_type: 模型的类型，可从枚举里找
        :param model_color: 实体的颜色
        :param longitude: 经度
        :param latitude: 维度
        :param altitude: 高度，地面物体可不填，默认为零，空中单位10左右的高度
        :param has_subnets: ture/false 是否显示子网相关按钮
        :param parent_id: 父节点的ID
        :param entity_switch: 实体开关，是否注销
        """
        self.entity_id = entity_id
        self.entity_name = entity_name
        self.model_type = model_type
        self.model_color = model_color
        self.has_subnets = has_subnets
        self.parent_id = parent_id
        self.entity_switch = entity_switch
        self.pos = ModelPos(longitude=longitude, latitude=latitude, altitude=altitude).to_protobuf()

    def set_pos(self, longitude, latitude, altitude):
        obj_pos = ModelPos(longitude=longitude, latitude=latitude, altitude=altitude).to_protobuf()
        self.pos = obj_pos

    def set_status(self, status=EnumStatus.normal):
        self.status = status

    def to_protobuf(self):
        obj_entity = net_entity(id=self.entity_id,
                                name=self.entity_name,
                                model_type=self.model_type,
                                model_color=self.model_color,
                                pos=self.pos,
                                parent_id=self.parent_id,
                                has_subnets=self.has_subnets,
                                entity_switch=self.entity_switch
                                )
        return obj_entity




class MapEdge(object):
    def __init__(self, src_id, dest_id, line_status=EnumEdgeStatus.create_active, line_type=EnumLineType.cable,
                 icon_type=None, line_width=0.2, line_color="red"):
        """
        定义两个实体之间的连线方式
        :param src_id: 原实体id
        :param dest_id: 目标实体id
        :param line_status: 线条的状态
        :param line_type: 连线类型
        :param icon_type: icon的类型
        :param line_width: 线宽
        :param line_color: 线的颜色
        """
        self.edge_id = "%s_%s" % (str(src_id), str(dest_id))
        self.src_id = src_id
        self.dest_id = dest_id
        self.line_status = line_status
        self.line_type = line_type
        self.icon_type = icon_type
        self.line_width = line_width
        self.line_color = line_color

    def to_protobuf(self):
        obj_edge = edge(
            edge_id=self.edge_id,
            src_id=self.src_id,
            dest_id=self.dest_id,
            line_status=self.line_status,
            line_type=self.line_type,
            line_icon=self.icon_type,
            line_width=self.line_width,
            line_color=self.line_color, )
        return obj_edge


class MapScene(object):
    def __init__(self):
        self.load_scene = {'entities': {}, 'edges': {}, 'marks':{}}
        self.entities = {}
        self.edges = {}
        self.marks = {}

    def add_load_scene(self, entity, edge, marks=[]):
        if isinstance(entity, list):
            for ent in entity:
                self.load_scene['entities'][ent.entity_id] = ent
        else:
            self.load_scene['entities'][entity.entity_id] = entity
        if isinstance(edge, list):
            for edg in edge:
                self.load_scene['edges'][edg.edge_id] = edg
        else:
            self.load_scene['edges'][edge.edge_id] = edge

        if isinstance(marks, list):
            for mark in marks:
                self.load_scene['marks'][mark.name] = mark
        else:
            self.load_scene['marks'] = marks

    def add_entity(self, entity):
        if isinstance(entity, list):
            for ent in entity:
                self.entities[ent.entity_id] = ent
        else:
            self.entities[entity.entity_id] = entity

    def add_edge(self, edge):
        if isinstance(edge, list):
            for edg in edge:
                self.edges[edg.edge_id] = edg
        else:
            self.edges[edge.edge_id] = edge

    def add_mark(self, marks):
        if isinstance(marks, list):
            for mark in marks:
                self.marks[mark.name] = mark
        else:
            self.marks[marks.name] = marks

    def to_binary(self):
        smq = SequenceMessageMaker()

        for ent in self.entities:
            smq.add_fragment(self.entities[ent].to_protobuf())
        for edg in self.edges:
            # print ','.join(['"%s":"%s"' % item for item in self.edges[edg].__dict__.items()])
            smq.add_fragment(self.edges[edg].to_protobuf())
        for mark in self.marks:
            smq.add_fragment(self.marks[mark].to_protobuf())

        # for edg_key in self.edges.keys():
        #     edge = self.edges.pop(edg_key)
        #     smq.add_fragment(edge.to_protobuf())
        # for ent_key in self.entities.keys():
        #     entity = self.entities.pop(ent_key)
        #     # entity = self.entities.pop(ent)
        #     smq.add_fragment(entity.to_protobuf())
        # for mark_key in self.marks.keys():
        #     mark = self.marks.pop(mark_key)
        #     smq.add_fragment(mark.to_protobuf())

        return smq.to_binary()

    def to_json(self):
        smq = SequenceMessageMaker()
        for ent in self.entities:
            # print ','.join(['"%s":"%s"' % item for item in self.entities[ent].__dict__.items()])
            smq.add_fragment(self.entities[ent].to_protobuf())
        for edg in self.edges:
            # print ','.join(['"%s":"%s"' % item for item in self.edges[edg].__dict__.items()])
            smq.add_fragment(self.edges[edg].to_protobuf())
        return smq.to_json()


if __name__ == "__main__":
    ent1 = MapEntity("p1", "Plane1", EnumModelType.war_plain, "red", "Radar1", 111, 2222)
    ent2 = MapEntity("p2", "Plane2", EnumModelType.radar, "R", "Radar2", 1451, 223)
    ent3 = MapEntity("p3", "Plane3", EnumModelType.aircraft_carrier, "R", "Radar2", 1451, 223)
    ent4 = MapEntity("p4", "Plane4", EnumModelType.command_center, "R", "Radar2", 1451, 223)
    edge1 = MapEdge("p1", "p2")
    edge2 = MapEdge("p1", "p3")
    edge3 = MapEdge("p1", "p4")
    edge4 = MapEdge("p3", "p4")
    ms = MapScene()
    ms.add_entity([ent1, ent2, ent3, ent4])
    ms.add_edge([edge1, edge2, edge3, edge4])
