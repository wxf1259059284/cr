# -*- coding: utf-8 -*-
from base.utils.error import Error
from base.utils.text import trans as _


MonitorError = Error(
    REQUIRED_FIELD=_('x_required_field'),
    NAME_HAVE_EXISTED=_('x_name_existed'),
    OUT_OF_RANGE=_('x_out_of_range'),
    LENGTH_ERROR=_("x_len_three"),
    TITLE_HAVE_EXISTED=_("x_name_existed"),
    TITLE_ERROR=_("x_english_num"),
    TITLE_HAVE_SPACE=_("x_name_not_spaces"),
    ILLEGAL_PARAMETER=_("x_illegal_parameter_value"),
    TLLEGAL_CODE=_("x_code_not_specifications"),
)
