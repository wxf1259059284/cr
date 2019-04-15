# -*- coding: utf-8 -*-
from base_mission.models import Mission
from base_mission.constant import MissionStatus
import logging
logger = logging.getLogger(__name__)


def inquire_mission_status(mission_id):
    """
    Inquire Mission`s mission status
    :param mission_id: mission id
    :return: mission_status
    """
    mission = Mission.objects.filter(id=mission_id).first()
    if mission:
        try:
            mission_status = mission.mission_status
        except Exception as e:
            logger.error(e)
            mission_status = MissionStatus.COMMING
    else:
        mission_status = MissionStatus.COMMING
        logger.error("Mission id[%s]: mission status not find", mission_id)

    return mission_status
