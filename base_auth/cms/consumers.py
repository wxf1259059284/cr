
from base.utils.websocket.base import Websocket

from base_auth.models import User


class UserWebsocket(Websocket):

    def get_connection_groups(self, message, **kwargs):
        return [self.user_group_name(message.user)]

    @classmethod
    def user_group_name(cls, user):
        if isinstance(user, User):
            user_id = user.id
        else:
            user_id = user

        return 'user-{user_id}'.format(user_id=user_id)

    @classmethod
    def user_send(cls, user, content, close=False, code=None):
        if isinstance(user, (list, tuple, set)):
            users = user
        else:
            users = [user]

        for usr in users:
            cls.group_send(cls.user_group_name(usr), content, close=close, code=code)
