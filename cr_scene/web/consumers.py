
from base.utils.enum import Enum
from base.utils.models.common import get_obj
from base_auth.cms.consumers import UserWebsocket
from cr_scene.models import CrEvent
from . import serializers as mserializers


class CrEventSceneWebsocket(UserWebsocket):

    Event = Enum(
        SCENE_START=1,
    )

    @classmethod
    def _get_cr_event_data(cls, user, cr_event):
        cr_event = get_obj(cr_event, CrEvent)
        data = mserializers.CrEventSerializers(cr_event, fields=('id',)).data
        return data

    @classmethod
    def cr_event_start(cls, user, cr_event):
        data = cls._get_cr_event_data(user, cr_event)
        cls.user_send(user, data, code=cls.Event.SCENE_START)
