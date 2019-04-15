
from base.utils.models.common import get_obj
from base_auth.models import User


def get_user(user):
    return get_obj(user, User)
