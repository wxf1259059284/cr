import logging

from rest_framework.response import Response

from base.utils.rest.mixins import CacheModelMixin, PublicModelMixin, PMixin
from rest_framework import filters, viewsets, status

from base_mission.utils.check_logger import SceneLogFactory
from base_mission.utils.object_attr import object_attr
from base_mission.check_api.parameter_validation import parameter_verification
from base_mission.check_api.status_description import record_status_information
from base_mission.web import serializers
from cr_scene import models as scene_models
from rest_framework import permissions
from base_mission import models as mission_model
from base_mission import constant
import ast

logger_critical = logging.getLogger(__name__)


class AgentViewSet(CacheModelMixin, PublicModelMixin,
                   PMixin, viewsets.ModelViewSet):
    queryset = scene_models.CrSceneEventUserAnswer.objects.all()
    serializer_class = serializers.AgentCheckSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('mission',)
    ordering_fields = ('last_edit_time',)
    ordering = ('-last_edit_time',)

    def create(self, request, *args, **kwargs):

        check_result = request.data
        scene_id = check_result.get("cr_event", None)
        mission_id = check_result.get("machine_id", None)
        result = check_result.get("result", None)

        if mission_id is None or scene_id is None or result is None:
            logger_critical.error("Agent Missing parameter: mission[%s], scene_id[%s], result[%s]",
                                  mission_id, scene_id, result)
            return Response(status=status.HTTP_200_OK)
        else:
            logger = SceneLogFactory(scene_id, __name__)

            mission = mission_model.Mission.objects.filter(id=mission_id).first()
            if mission:
                logger.info("Mission[%s]: Agent check OK", mission.title)
                logger.debug("Mission[%s]:  Check result [%s]", mission.title, result)

                if mission.mission_status == constant.MissionStatus.STOP:
                    record_status_information(
                        mission,
                        "mission is stop",
                    )
                    logger.error("Mission[%s]: mission is stop", mission.title)

                    return Response(status=status.HTTP_200_OK)
                else:
                    try:
                        result = ast.literal_eval(result)
                        self.write_log_table(result, scene_id, mission, logger)
                    except Exception:
                        self.write_log_table(result, scene_id, mission, logger)

            else:
                logger.error("[create]No mission, Id is %s", mission_id)

        return Response(status=status.HTTP_200_OK)

    def write_log_table(self, result, scene_id, mission, logger):
        cr_scene = None

        is_solved = self.judge_right_wrong(result)
        logger.info("Mission[%s]: agent result: %s ", mission.title, is_solved)

        cr_event_scene = scene_models.CrEventScene.objects.filter(cr_scene_instance=scene_id).first()
        if cr_event_scene:
            scene_models.CrSceneAgentMissionLog.objects.create(
                mission_id=mission.id,
                cr_event=cr_event_scene.cr_event,
                result=result.get("msg", '') if type(result) == dict else result,
                is_solved=is_solved,
            )
        else:
            cr_scene = scene_models.CrScene.objects.filter(scene_id=scene_id).first()

            scene_models.CmsAgentTestCheckLog.objects.create(
                mission_id=mission.id,
                cr_scene=cr_scene,
                result=result.get("msg", '') if type(result) == dict else result,
                is_solved=is_solved,
            )

        if is_solved:
            self.record_results_database(cr_scene, mission, cr_event_scene, logger)

    def record_results_database(self, cr_scene, mission, cr_event_scene, logger):
        record_status_information(
            mission,
            "Agent check success",
        )
        logger.info("Mission[%s]: Agent check success", mission.title)

        if mission:
            mission_score = mission.score
            check_mission = object_attr(mission, "checkmission")
            if check_mission is None:
                return False
            agent_mission_list = ["is_once", "is_polling", "scripts"]
            agent_mission_data = parameter_verification(check_mission, agent_mission_list)
            if agent_mission_data is {}:
                return False

            if cr_event_scene:
                record = scene_models.CrSceneEventUserAnswer.objects.filter(mission=mission.id)
                if not record.exists():
                    scene_models.CrSceneEventUserAnswer.objects.create(
                        mission=mission,
                        score=float(mission_score),
                        cr_event=cr_event_scene.cr_event,
                    )
                else:
                    if agent_mission_data.get("is_once"):
                        return False
                    else:
                        if agent_mission_data.get("is_polling"):
                            _score = float(record.first().score + float(mission_score))
                            record.update(score=_score)
                        else:
                            return False
            else:
                record = scene_models.CmsTestCheckRecord.objects.filter(mission=mission.id)
                if not record.exists():
                    scene_models.CmsTestCheckRecord.objects.create(
                        mission=mission,
                        score=float(mission_score),
                        cr_scene=cr_scene if cr_scene else None,
                        script=agent_mission_data.get("scripts"),
                        target_ip=agent_mission_data.get("scripts")
                    )
                else:
                    if agent_mission_data.get("is_once"):
                        return False
                    else:
                        if agent_mission_data.get("is_polling"):
                            _score = float(record.first().score + float(mission_score))
                            record.update(score=_score)
                        else:
                            return False
        else:
            logger.error("[record_results_database]No mission")

    def judge_right_wrong(self, result):
        if type(result) == str or type(result) == unicode:
            if 'CheckUp' in result:
                is_solved = True
            else:
                is_solved = False

        elif type(result) == dict:
            if "check" in result:
                if result.get("check") == "success":
                    is_solved = True
                else:
                    is_solved = False
            else:
                is_solved = False

        else:
            is_solved = False

        return is_solved
