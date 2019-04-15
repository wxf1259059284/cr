# -*- coding: utf-8 -*-
from base.utils.enum import Enum
from base.utils.thread import async_exe
from cr_scene.utils.scene_util import get_scene_by_id
from traffic_event.utils.traffic_event_manager import TrafficEventManager


class SceneTrafficManager(object):
    ActionType = Enum(
        START=0,
        STOP=1,
    )

    # flag=true 表示前台， flag=false 表示后台
    def __init__(self, scene_id, flag=True):
        self.scene_id = scene_id
        self.cr_scene = get_scene_by_id(scene_id, flag)

    def start_traffic_event(self):
        return self._handle_cr_scene_traffic(self.ActionType.START)

    def stop_traffic_event(self):
        return self._handle_cr_scene_traffic(self.ActionType.STOP)

    def _handle_cr_scene_traffic(self, action):
        if not self.cr_scene or not self.cr_scene.traffic_events.all().first():
            return
        traffic_events = self.cr_scene.traffic_events.all()
        for traffic_event in traffic_events:
            traffifc_manager = TrafficEventManager(traffic_event, self.scene_id)

            if action == self.ActionType.START:
                async_exe(traffifc_manager.start(), (), delay=2)

            elif action == self.ActionType.STOP:
                async_exe(traffifc_manager.stop(), ())
            else:
                pass
