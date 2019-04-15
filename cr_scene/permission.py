# -*- coding: utf-8 -*-
import functools
import json
import logging

from datetime import datetime
from django.http.request import QueryDict
from django.utils.translation import ugettext_lazy as _
from rest_framework import permissions, exceptions

from base.utils.enum import Enum
from cr_scene import app_settings
from cr_scene.cms.serializers import CrEventSceneSeriallizer
from cr_scene.models import CrEventScene, CrEvent
from cr_scene.web.serializers import CrEventDetailSerializers as webCrEventDetailSerializers

logger = logging.getLogger(__name__)

TYPE = Enum(
    ADMIN=1,
    REFEREE=2
)


# 检查cr_event对象是否可以访问
def cheker_cr_event_obj(fun):
    @functools.wraps(fun)
    def wrapper(*args, **kwargs):
        ret = fun(*args, **kwargs)

        request = args[1]
        cr_event_obj = args[3]

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        flag = now > cr_event_obj.start_time.strftime('%Y-%m-%d %H:%M:%S')
        _user_is_admin = request.data.get('_user_is_admin', False)

        if flag is False and _user_is_admin is False:
            # 管理员不在此判断内
            logger.info('now < start_time, this cr event is not start')
            raise exceptions.PermissionDenied(detail='Not Start!')
        return ret

    return wrapper


# 允许修改request.data里面的数据
def modify_request_data(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        request = args[1]
        if isinstance(request.data, QueryDict):
            request.data._mutable = True
        ret = func(*args, **kwargs)
        if isinstance(request.data, QueryDict):
            request.data._mutable = False
        return ret

    return wrapper


# 检查参数
def checker_params(request, obj=None, parmas=None):
    parmas = 'cr_event_id' if parmas is None else parmas

    cr_event_id = request.data.get(parmas, None) or request.query_params.get(parmas, None)

    if obj and isinstance(obj, CrEvent):
        cr_event_id = obj.id

    if not cr_event_id:
        logger.error('{} is None'.format(parmas))
        return False, None
    return True, cr_event_id


class HasPermissionMixin(object):

    def has_permission(self, request, view):
        parmas = getattr(view, 'permission_query_param', 'cr_event_id')
        flag, cr_event_id = checker_params(request, parmas=parmas)
        if flag is False:
            return False

        return self.base_permission(request, cr_event_id)


class HasObjPermissionMixin(object):
    """
    对象级别的权限
    """

    def has_object_permission(self, request, view, obj):
        flag, cr_event_id = checker_params(request, obj)
        if flag is False:
            return False

        return self.base_permission(request, cr_event_id)


class CustomBasePermission(permissions.BasePermission):
    """
    权限基础类
    """
    default_user_position = TYPE.ADMIN  # 设置默认职位

    @modify_request_data
    def base_permission(self, request, cr_event_id):
        # 管理员和裁判都可以访问
        # _user_is_admin True 是管理员, False 裁判或者普通用户
        flag, scene_ids, return_cr_event_scenes, user_is_admin = self.has_cr_event_permission_and_record_data(
            cr_event_id, request)

        request.data['_permission_scene_ids'] = scene_ids and scene_ids or None
        request.data['_permission_cr_event_scene_data'] = return_cr_event_scenes
        request.data['_user_is_admin'] = user_is_admin

        return flag

    def has_cr_event_permission_and_record_data(self, cr_event_id, request):
        flag = False
        user_is_admin = False
        scene_ids = []
        return_cr_event_scenes = []

        user = request.user
        cr_event_scenes = CrEventSceneSeriallizer(CrEventScene.objects.filter(cr_event_id=cr_event_id), many=True).data
        if len(cr_event_scenes) > 0:

            if app_settings.CHECKER_ONE_AS_ADMIN is True:
                return_cr_event_scenes = cr_event_scenes
                for cr_event_scene in cr_event_scenes:
                    scene_ids.append(cr_event_scene['cr_scene'])
                    roles = json.loads(cr_event_scene['roles'])

                    for role in roles:
                        if self.user_in_roles(role, user) and flag is False:
                            if role['role'] == TYPE.ADMIN and user_is_admin is False:
                                user_is_admin = True
                            flag = True
                            break
            else:
                for cr_event_scene in cr_event_scenes:
                    roles = json.loads(cr_event_scene['roles'])

                    for role in roles:
                        if self.user_in_roles(role, user):
                            if role['role'] == TYPE.ADMIN and user_is_admin is False:
                                user_is_admin = True
                            scene_ids.append(cr_event_scene['cr_scene'])
                            return_cr_event_scenes.append(cr_event_scene)
                            flag = True

        return flag, scene_ids, return_cr_event_scenes, user_is_admin

    def user_in_roles(self, role, user):
        if self.default_user_position == TYPE.ADMIN:
            return self._admin(role, user)
        elif self.default_user_position == TYPE.REFEREE:
            return self._referee(role, user)
        else:
            raise exceptions.ValidationError('USER_TYPE is not in the TYPE, please checker again')

    def _admin(self, role, user):
        return role['role'] == TYPE.ADMIN and user.id in role['users']

    def _referee(self, role, user):
        return role['role'] in TYPE.values() and user.id in role['users']


class RefereePermission(HasObjPermissionMixin, CustomBasePermission):
    """
    针对cr_event对象级别的
    裁判和管理员都能访问
    """
    message = _('x_general_user_is_not_allow')
    default_user_position = TYPE.REFEREE

    @cheker_cr_event_obj
    def has_object_permission(self, request, view, obj):
        return super(RefereePermission, self).has_object_permission(request, view, obj)


class RefereeNoObjectPermission(HasPermissionMixin,
                                CustomBasePermission):
    """
    不针对对象级别的权限
    管理员和裁判可以访问
    """
    message = _('x_general_user_is_not_allow')
    default_user_position = TYPE.REFEREE


class AdministratorPermission(HasObjPermissionMixin,
                              CustomBasePermission):
    """
    针对cr_event对象级别的
    管理员可以访问
    """
    message = _("x_general_user_and_referee_is_not_allow")

    # default_user_position = TYPE.ADMIN

    @cheker_cr_event_obj
    def has_object_permission(self, request, view, obj):
        return super(AdministratorPermission, self).has_object_permission(request, view, obj)


class AdministratorNoObjectPermission(HasPermissionMixin,
                                      CustomBasePermission):
    """
    不针对对象级别的权限
    仅管理员可以访问
    """
    message = _("x_general_user_and_referee_is_not_allow")
    # default_user_position = TYPE.ADMIN


class BasePermission(permissions.BasePermission):

    def _check_user_cr_event_scenes(self, request, cr_event_scenes):
        user = request.user
        if not len(cr_event_scenes) > 0:
            logger.error('not get cr_event_scene data')
            return False

        for cr_event_scene in cr_event_scenes:
            roles = json.loads(cr_event_scene.get('roles', '[]'))
            for role in roles:
                if self.user_in_row(role, user):
                    self._is_admin(request, role, user)
                    return True

    def user_in_row(self, role, user):
        return user.id in role['users']

    @modify_request_data
    def _is_admin(self, request, role, user):
        # 判断是否是该实例下的管理员
        request.data['_user_is_admin'] = role['role'] == TYPE.ADMIN and user.id in role['users']
        logger.info('add key user_is_admin status is ==> {}'.format(request.data.get('_user_is_admin')))

    def get_cr_event_scenes(self, request, cr_event_id, **kwargs):
        raise NotImplementedError('.get_cr_event_scenes() must be overridden.')

    @cheker_cr_event_obj
    def has_object_permission(self, request, view, obj):
        flag, cr_event_id = checker_params(request, obj)
        if flag is False:
            return False

        cr_scene_id = view.kwargs.get('cr_scene_id', None)
        # if cr_scene_id is None:
        #     return False

        cr_event_scenes = self.get_cr_event_scenes(request, cr_event_id, cr_scene_id=cr_scene_id)
        flag = self._check_user_cr_event_scenes(request, cr_event_scenes)

        if flag is not True:
            return False
        return flag

    def has_permission(self, request, view):
        parmas = getattr(view, 'permission_query_param', 'cr_event_id')
        flag, cr_event_id = checker_params(request, parmas=parmas)
        if flag is False:
            self.message = 'you must provide parameter {} in this api'.format(parmas)
            return False

        if not cr_event_id.isdigit():
            self.message = '{} is error type, is must be int'.format(parmas)
            return False

        cr_event_scenes = self.get_cr_event_scenes(request, cr_event_id=cr_event_id)
        flag = self._check_user_cr_event_scenes(request, cr_event_scenes)

        if flag is not True:
            return False
        return flag


class AllPeopleInCrEventPermission(BasePermission):
    """
    针对对象级别的权限
    该实例下的所有人可以访问, 未开始只有管理员可以访问
    """
    message = _("x_this_event_allow_this_event_people_allow")

    @modify_request_data
    def get_cr_event_scenes(self, request, cr_event_id, **kwargs):
        cr_event = webCrEventDetailSerializers(CrEvent.objects.get(pk=cr_event_id), context={'request': request}).data
        request.data['_permission_cr_event'] = cr_event
        return cr_event['cr_event_scenes']

    def has_permission(self, request, view):
        return True


class CrEventAllowAnyNoObjPermission(BasePermission):
    """
    不针对对象级别的权限
    该实例下的所有人可以访问
    """
    message = _("x_this_event_allow_this_event_people_allow")

    def get_cr_event_scenes(self, request, cr_event_id, **kwargs):
        cr_event_scenes = CrEventSceneSeriallizer(CrEventScene.objects.filter(cr_event_id=cr_event_id), many=True).data
        return cr_event_scenes

    def has_object_permission(self, request, view, obj):
        return True


class OnlyOneCrSceneInCrEventPermission(BasePermission):
    """
    针对对象级别的权限
    判断实例下的一个场景是否具有访问权限
    """
    message = _("x_no_permission_to_access_a_scene_under_the_event")

    def has_permission(self, request, view):
        return True

    @modify_request_data
    def get_cr_event_scenes(self, request, cr_event_id, **kwargs):
        cr_scene_id = kwargs.get("cr_scene_id", None)
        if cr_scene_id is None:
            raise exceptions.ValidationError('in this permmission we must need cr_scene_id params')
        request.data['cr_scene_id'] = cr_scene_id
        cr_event = webCrEventDetailSerializers(CrEvent.objects.get(pk=cr_event_id), context={'request': request}).data
        request.data['_permission_cr_event'] = cr_event
        return cr_event['cr_event_scenes']


class OnlyOrdinaryWithCrScenePermission(BasePermission):
    """
    针对对象级别的权限
    判断某个实例下对应的单个场景下的只有普通用户才能访问权限
    """
    message = _("x_corresponding_single_scene_in_the_event_can_only_be_accessed_by_ordinary_users")

    @modify_request_data
    def get_cr_event_scenes(self, request, cr_event_id, **kwargs):
        cr_scene_id = kwargs.get("cr_scene_id", None)
        if cr_scene_id is None:
            raise exceptions.ValidationError('in this permmission we must need cr_scene_id params')
        request.data['cr_scene_id'] = cr_scene_id
        cr_event = webCrEventDetailSerializers(CrEvent.objects.get(pk=cr_event_id), context={'request': request}).data
        request.data['_permission_cr_event'] = cr_event
        return cr_event['cr_event_scenes']

    def has_permission(self, request, view):
        return True

    def user_in_row(self, role, user):
        return role['role'] not in TYPE.values() and user.id in role['users']
