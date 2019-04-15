# -*- coding: utf-8 -*-
from channels.routing import include
from channels.routing import route

from base.utils.app import get_base_routers
from base_mission.check_api import channels_task
from base_traffic.traffic.delay_traffic import delay_traffic
from base_evaluation.delay_evaluation import evaluation_push


routerpatterns = [
    route('control', channels_task.control_message),
    route('traffic', delay_traffic),
    route('evaluation', evaluation_push),
]

base_routers = get_base_routers()
if base_routers:
    routerpatterns.append(include(base_routers, path=r'^/ws'))
