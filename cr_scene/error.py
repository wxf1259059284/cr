# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from base.utils.error import Error
from base.utils.text import trans as _

error = Error(
    MISSING_PARAMETERS=_('x_missing_parameters'),
    ONLY_EXAM=_('x_only_exam'),
    HAS_DOWN=_('x_has_down'),
    IS_NUMBER=_('x_is_number'),
    NOT_FOUND=_('x_not_found'),
    CHECK_NOT_COMMIT=_('x_check_not_commit'),
    NAME_EXISTS=_('x_name_exists'),
    IS_RUNNING=_('x_event_is_running'),
    SCENE_ID_IS_NOT_ALLOW=_('x_scene_id_is_not_allow'),
    CR_SCENE_INSTANCE_IS_NONE=_('x_cr_scene_instance_is_none'),
    CONNECTION_REFUSED=_('x_connection_refused'),
    PARAMETER_SYNTAX_ERROR=_('x_parameter_syntax_error'),
    START_TIME_IS_GREATER_THAN_END_TIME=_('x_start_time_is_greater_than_end_time'),
    FIELD_LENGTH_CANNOT_EXCEED=_('x_field_length_cannot_exceed'),  # 传参的使用不了
    XSS_ATTACK=_('x_XSS_attack'),
    SELECT_AT_LEAST_ONE_SCENE=_('x_select_at_least_one_scene'),
    LOGO_CAN_NOT_BE_EMPTY=_('x_logo_can_not_be_empty'),
    UNFINISHED_MISSION_CANNOT_MODIFY_SCORES=_("x_unfinished_mission_cannot_modify_scores"),
    SUBMIT_SCORE_MUST_BE_GREATER_THAN_0=_("x_submit_score_must_be_greater_than_0"),
    the_scene_id_does_not_belong_to_the_crevent=_("x_the_scene_id_does_not_belong_to_the_crevent"),
    MISS_PARAMETER=_("x_mission_parameter_error"),
    SITUATION_SERVICE_NOT_START_CALL_ADMIN=_("x_situation_service_not_start_call_admin"),
    OPERATION_FAILED=_("x_operation_failed"),
    VIS_START_FAILED=_("x_vis_start_failed_call_admin"),
)
