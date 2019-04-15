# -*- coding: utf-8 -*-
from base_mission.check_open_api import RpcChecked, AgentChecked
from base_mission.constant import CheckType
from base_mission.utils.object_attr import object_attr


def control_message(message):
    """
    delay mission
    :param message: parameter
    :return:
    """
    content = object_attr(message, "content")

    mission_check = None
    if content.get("check_type") == CheckType.SYSTEM:
        mission_check = RpcChecked(content)
    elif content.get("check_type") == CheckType.AGENT:
        mission_check = AgentChecked(content)
    else:
        pass

    if mission_check:
        mission_check.run()
