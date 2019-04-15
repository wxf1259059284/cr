# -*- coding: utf-8 -*-
from base_mission import constant
from base_mission.utils.check_logger import SceneLogFactory
from base_mission.utils.object_attr import object_attr
from base_mission.check_api.status_description import record_status_information
from base_mission.check_api.get_script_parameter import kwargs_process
from base_mission.check_api.delivering_task import start_checker
from base_mission.constant import MissionStatus
from base_mission.check_api.parameter_validation import parameter_verification
from base_mission.check_api.misson_status import inquire_mission_status
from cr_scene import models as cr_scene_models


class ResultProcess(object):
    def __init__(self, message, ret):
        self.message_original = message
        self.ret = ret
        self.title = self.message.get("title", None)
        self.logger = SceneLogFactory(message.get("scene_id", "default"), __name__)
        self.message = message

    def check_over(self, mission):
        """
        check over do something, Write database,is polling
        :return:
        """
        parameter_list = ["scene_id", "script", "id", "check_type",
                          "target_ip", "checker_ip", "is_polling",
                          "title", "score", "is_once", "interval",
                          "checker_port", "scene_name"]

        self.message = parameter_verification(self.message_original, parameter_list)

        if not self.message:
            self.logger.error("Parameter Missing")
            # 有问题
            record_status_information(self.message_original.get("id"),
                                      "Parameter Missing",
                                      MissionStatus.STOP)
            return

        script = self.message.get('script')
        mission_id = self.message.get("id")

        # 记录状态
        self.logger.info("Mission[%s]: Check status %s, [%s]",
                         self.message.get("title"), self.ret.get("status", None), self.ret.get("content"))

        # Write to the log database
        self.record_results(script)

        # Whether to continue and Write result database
        is_continue = self.polling_results(script)

        self._check_is_continue(mission, is_continue, mission_id, script)

    def polling_results(self, script):
        """
        polling results, judge whether to continue execution
        :param script:
        :return: False:stop polling, True: continue polling
        """
        if self.ret.get("status", None) in ["ok", "up"]:
            results = self.calculation_results(script)

        else:
            results = False
        results_is_poll = self.is_polling(results)
        return results_is_poll

    def is_polling(self, results):
        """
        Judging is to continue
        :param results:
        :return:
        """
        continue_check = True
        stop_check = False

        if results:
            self.record_check_scores()
            if not self.message.get("is_polling"):
                return stop_check
            else:
                return self.message.get("is_polling")
        else:
            self.logger.info("Mission[%s]: Check fail!", self.message.get("title"))

            return continue_check

    def calculation_results(self, script):
        """
        Judge the result of the check
        :param script:
        :return: results(True, False)
        """
        if script.split(".")[-1] == "py":
            results = True if self.ret["content"].get("check") == "success" else False
        else:
            results = True if "CheckUp" in self.ret["content"] else False
        return results

    def record_results(self, script):
        """
        write result in databases(cr_scene_models.CmsTestCheckLog)
        :param script:script name
        :return:
        """
        if self.ret.get("status", None) in ["ok", "up"]:
            results = self.calculation_results(script)

            score = self.message.get("score") if results else 0

        else:
            results = False
            score = 0

        scene_id = self.message.get("scene_id")
        cr_event_scene = cr_scene_models.CrEventScene.objects.filter(cr_scene_instance=scene_id).first()
        if cr_event_scene:
            cr_scene_models.CrSceneMissionCheckLog.objects.create(
                mission_id=self.message["id"],
                score=float(self.message["score"]),
                cr_event=cr_event_scene.cr_event if cr_event_scene.cr_event else None,
                is_solved=results,
                target_ip=self.message.get('target_ip'),
                script=self.message.get('script'),
            )
        else:
            cr_scene = cr_scene_models.CrScene.objects.filter(scene_id=scene_id).first()

            cr_scene_models.CmsTestCheckLog.objects.create(
                mission_id=self.message.get("id"),
                target_ip=self.message.get('target_ip'),
                cr_scene=cr_scene if cr_scene else None,
                is_solved=results,
                score=score,
                script=script,
            )

        self.logger.debug("Mission[%s]: Write data to the log table", self.title)

    def record_check_scores(self):
        """
        write check Grade in databases(cr_scene_models.CmsTestCheckRecord)
        :return:
        """
        scene_id = self.message["scene_id"]
        cr_event_scene = cr_scene_models.CrEventScene.objects.filter(cr_scene_instance=scene_id).first()
        if not cr_event_scene:
            record = cr_scene_models.CmsTestCheckRecord.objects.filter(mission=self.message.get("id"))
            if not record.exists():
                cr_scene = cr_scene_models.CrScene.objects.filter(scene_id=scene_id).first()

                cr_scene_models.CmsTestCheckRecord.objects.create(
                    mission_id=self.message["id"],
                    score=float(self.message["score"]),
                    cr_scene=cr_scene if cr_scene else None,
                    target_ip=self.message.get('target_ip'),
                    script=self.message.get('script'),
                )
            else:
                _score = float(record.first().score + float(self.message.get("score")))
                record.update(score=_score)

        else:
            record = cr_scene_models.CrSceneEventUserAnswer.objects.filter(mission=self.message.get("id"))

            if not record.exists():
                cr_scene_models.CrSceneEventUserAnswer.objects.create(
                    mission_id=self.message["id"],
                    score=float(self.message["score"]),
                    cr_event=cr_event_scene.cr_event if cr_event_scene.cr_event else None,
                )
            else:
                _score = float(record.first().score) + self.message.get("score")
                record.update(score=_score)

        self.logger.debug("Mission[%s]: Check success! Write data"
                          "to the result table", self.message.get("title"))
        return True

    def _check_is_continue(self, mission, is_continue, mission_id, script):
        """
        Determine if check functions continues
        :param is_continue: is continue
        :param mission_id: mission id
        :param script: script name
        :return:
        """
        if mission:
            if is_continue:
                mission_status = inquire_mission_status(mission_id)

                if mission_status != MissionStatus.STOP and not self.message.get("is_once"):
                    self.logger.info("Mission[%s]: Check carry on", self.message.get("title"))

                    params = mission.checkmission.params if object_attr(mission.checkmission,
                                                                        "params") else self.message.get("params")

                    self.message = kwargs_process(self.message, params)

                    self.message.update({
                        "first_check_time": mission.checkmission.interval if mission.checkmission.interval else 0,
                        "is_once": mission.checkmission.is_once,
                        "is_polling": mission.checkmission.is_polling
                    })

                    start_checker(self.message, self.logger, False)
                else:
                    record_status_information(
                        mission,
                        "Check over",
                        constant.MissionStatus.STOP
                    )
                    self.logger.info("Mission[%s]: Check over", self.message.get("title"))
            else:
                record_status_information(
                    mission,
                    "Check over",
                    constant.MissionStatus.STOP
                )
                self.logger.info("Mission[%s]: Check over", self.message.get("title"))
        else:
            self.logger.error("Mission[%s]: Mission id is None", self.message.get("title"))
