# -*- coding: utf-8 -*-
from base.utils.error import Error
from base.utils.text import trans as _


TrafficError = Error(
    REQUIRED_FIELD=_('x_required_field'),
    NAME_HAVE_EXISTED=_('x_name_existed'),
    OUT_OF_RANGE=_('x_out_of_range'),
    INVALID_CHARACTER=_('x_invalid_character'),
    FIELD_INVALID=_('x_field_invalid'),
    PLEASE_UPLOAD_PCAP=_('x_please_upload_pcap'),
    CATEGORY_BE_USED=_('x_category_be_used')
)
