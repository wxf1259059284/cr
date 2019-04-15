# -*- coding: utf-8 -*-
import logging

from rest_framework import permissions, exceptions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from base.utils.rest.decorators import request_data

from base_scene.models import SceneTerminal
from base_scene.common.scene import SceneHandler

from .error import error


logger = logging.getLogger(__name__)


# 虚拟机上报状态
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
@request_data(strict=True)
def report_server_status(request):
    try:
        scene_id = request.shift_data.get('scene', int)
        server_id = request.shift_data.get('server')
        server_status = request.shift_data.get('status', int)
    except Exception as e:
        logger.error('invalid params[%s]: %s' % (request.data, e))
        raise exceptions.ParseError(error.INVALID_PARAMS)

    if server_status not in SceneTerminal.Status.values():
        raise exceptions.ValidationError(error.INVALID_PARAMS)
    else:
        logger.info('report server status [scene=%s, server=%s, status=%s]' % (scene_id, server_id, server_status))

    try:
        scene_terminal = SceneTerminal.objects.get(scene=scene_id, sub_id=server_id)
    except SceneTerminal.DoesNotExist as e:
        raise exceptions.NotFound(error.TERMINAL_NOT_FOUND)

    handler = SceneHandler(scene_terminal.scene.user, scene=scene_terminal.scene)
    try:
        handler.scene_util.report_terminal_status(scene_terminal, server_status)
    except Exception as e:
        logger.error('terminal[server=%s] save error: %s', server_id, e)
        raise exceptions.APIException(error.ERROR)

    return Response()
