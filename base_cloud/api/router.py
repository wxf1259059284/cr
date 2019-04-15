# -*- coding: utf-8 -*-

from base_cloud.complex.views import BaseScene


class Router(object):

    def __init__(self, operator=None):
        self.operator = operator or BaseScene()

    def get(self, router_id):
        self.operator.get_router(router_id)

    def create(self, name, **kwargs):
        static_routing = kwargs.pop('static_routing', [])
        router = self.operator.scene_create_router(name=name, **kwargs)
        for routing in static_routing:
            newroute = self._convert_static_route(routing)
            self.operator.add_static_route(router['id'], newroute)

        return router

    def delete(self, router_id):
        try:
            self.operator.scene_delete_router(router_id)
        except Exception:
            pass

    def add_static_route(self, router_id, static_route):
        route = self._convert_static_route(static_route)
        self.operator.add_static_route(router_id, route)

    def remove_static_route(self, router_id, static_route):
        route = self._convert_static_route(static_route)
        self.operator.remove_static_route(router_id, [route])

    def _convert_static_route(self, static_route):
        return {
            'destination': static_route.get('destination'),
            'nexthop': static_route.get('gateway'),
        }
