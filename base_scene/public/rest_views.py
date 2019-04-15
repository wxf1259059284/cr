# -*- coding: utf-8 -*-
import json
import logging

from rest_framework import permissions, exceptions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from base.utils.rest.decorators import request_data

from base_scene.models import SceneGateway
from base_scene.common.exceptions import SceneException
from base_scene.common.scene import SceneHandler


from .error import error

logger = logging.getLogger(__name__)


@api_view(['POST', 'DELETE'])
@permission_classes((permissions.IsAuthenticated,))
@request_data()
def gateway_static_route(request):
    if request.method == 'POST':
        try:
            scene_id = request.shift_data.get('scene', int)
            gateway_id = request.shift_data.get('gateway')
            static_route = json.loads(request.shift_data.get('static_route'))
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        try:
            scene_gateway = SceneGateway.objects.get(scene=scene_id, sub_id=gateway_id)
        except SceneGateway.DoesNotExist as e:
            raise exceptions.NotFound(error.GATEWAY_NOT_FOUND)

        gateway_util = SceneHandler(request.user).get_gateway_util(scene_gateway)
        try:
            gateway_util.add_static_routing(static_route)
        except SceneException as e:
            raise exceptions.PermissionDenied(e.message)

        return Response(status=status.HTTP_201_CREATED)
    elif request.method == 'DELETE':
        try:
            scene_id = request.shift_data.get('scene', int)
            gateway_id = request.shift_data.get('gateway')
            static_route = json.loads(request.shift_data.get('static_route'))
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        try:
            scene_gateway = SceneGateway.objects.get(scene=scene_id, sub_id=gateway_id)
        except SceneGateway.DoesNotExist as e:
            raise exceptions.NotFound(error.GATEWAY_NOT_FOUND)

        gateway_util = SceneHandler(request.user).get_gateway_util(scene_gateway)
        try:
            gateway_util.remove_static_routing(static_route)
        except SceneException as e:
            raise exceptions.PermissionDenied(e.message)

        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST', 'DELETE'])
@permission_classes((permissions.IsAuthenticated,))
@request_data()
def gateway_firewall_rule(request):
    if request.method == 'POST':
        try:
            scene_id = request.shift_data.get('scene', int)
            gateway_id = request.shift_data.get('gateway')
            firewall_rule = json.loads(request.shift_data.get('firewall_rule'))
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        try:
            scene_gateway = SceneGateway.objects.get(scene=scene_id, sub_id=gateway_id)
        except SceneGateway.DoesNotExist as e:
            raise exceptions.NotFound(error.GATEWAY_NOT_FOUND)

        gateway_util = SceneHandler(request.user).get_gateway_util(scene_gateway)
        try:
            gateway_util.add_firewall_rule(firewall_rule)
        except SceneException as e:
            raise exceptions.PermissionDenied(e.message)

        return Response(status=status.HTTP_201_CREATED)
    elif request.method == 'DELETE':
        try:
            scene_id = request.shift_data.get('scene', int)
            gateway_id = request.shift_data.get('gateway')
            firewall_rule = json.loads(request.shift_data.get('firewall_rule'))
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        try:
            scene_gateway = SceneGateway.objects.get(scene=scene_id, sub_id=gateway_id)
        except SceneGateway.DoesNotExist as e:
            raise exceptions.NotFound(error.GATEWAY_NOT_FOUND)

        gateway_util = SceneHandler(request.user).get_gateway_util(scene_gateway)
        try:
            gateway_util.remove_firewall_rule(firewall_rule)
        except SceneException as e:
            raise exceptions.PermissionDenied(e.message)

        return Response(status=status.HTTP_204_NO_CONTENT)
