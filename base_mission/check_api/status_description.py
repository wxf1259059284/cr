from base_mission.error import error
from base_mission.constant import MissionStatus
from base_mission.utils.object_attr import object_attr
from base_mission.models import Mission
import logging
logger = logging.getLogger(__name__)


def record_status_information(mission_id, info, status=None):
    """
    Change Mission Status;Record mission information; Write Log
    :param mission_id: mission id or mission(object)
    :param info: mission information
    :param status: mission status
    :return:
    """
    if type(mission_id) not in [long, str, int]:
        if object_attr(mission_id, "checkmission"):
            mission_id.checkmission.status_description = info
            mission_id.checkmission.save()
            if status is None:
                pass
            elif int(status) in list(MissionStatus.source.values()):
                _change_status(mission_id, status)
            else:
                raise Exception.ValidationError(error.MISSION_STATUS_ERROR)
    else:
        mission = Mission.objects.filter(id=mission_id).first()
        if mission:
            if object_attr(mission, "checkmission"):
                mission.checkmission.status_description = info
                mission.checkmission.save()
                if status is None:
                    pass
                elif int(status) in list(MissionStatus.source.values()):
                    _change_status(mission, status)
                else:
                    raise Exception.ValidationError(error.MISSION_STATUS_ERROR)


def _change_status(mission, status):
    """
    Change mission status; Write information to the Log
    :param mission: mission
    :param status: mission status
    :return:
    """
    mission.mission_status = status
    mission.save()
