# -*- coding: utf-8 -*-
from base_auth.cms.consumers import UserWebsocket
from base.utils.enum import Enum

UpgradeStatus = Enum(
    PREPARING=0,
    RAISEBAK=1,
    UPGRADE=2,
    REMOVEBAK=3,
    FINISH=4,
    FAIL=5,
)


class UpgradeVersionWebsocket(UserWebsocket):

    @classmethod
    def send_upgrade_status(cls, user, code, info=''):
        cls.user_send(user, info, code=code)
