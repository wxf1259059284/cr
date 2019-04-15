# -*- coding: utf-8 -*-

# 根据guacamole数据表配置的模型


from __future__ import unicode_literals

from django.db import models
from django.utils import timezone

from base.utils.enum import Enum


# 指定guacamole对应数据库
class GuacamoleManager(models.Manager):
    def __init__(self):
        super(GuacamoleManager, self).__init__()
        self._db = 'guacamole'


# 连接分组
class GuacamoleConnectionGroup(models.Model):
    connection_group_id = models.IntegerField(primary_key=True)
    connection_group_name = models.CharField(max_length=128)
    parent = models.ForeignKey('self', null=True, related_name='+')
    Type = Enum(
        ORGANIZATIONAL='ORGANIZATIONAL',
        BALANCING='BALANCING',
    )
    type = models.CharField(max_length=32, default=Type.ORGANIZATIONAL)
    max_connections = models.IntegerField(null=True)
    max_connections_per_user = models.IntegerField(null=True)
    enable_session_affinity = models.BooleanField(default=False)
    objects = GuacamoleManager()

    class Meta:
        unique_together = (('connection_group_name', 'parent'), )
        db_table = 'guacamole_connection_group'
        managed = False


# 连接
class GuacamoleConnection(models.Model):
    connection_id = models.AutoField(primary_key=True)
    connection_name = models.CharField(max_length=128)
    parent = models.ForeignKey(GuacamoleConnectionGroup, on_delete=models.CASCADE, null=True)
    protocol = models.CharField(max_length=32)
    max_connections = models.IntegerField(null=True)
    max_connections_per_user = models.IntegerField(null=True)
    objects = GuacamoleManager()

    class Meta:
        unique_together = (('connection_name', 'parent'), )
        db_table = 'guacamole_connection'
        managed = False


# guacamole自有用户
class GuacamoleUser(models.Model):
    user_id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=128, unique=True)
    password_hash = models.BinaryField(max_length=32)
    password_salt = models.BinaryField(max_length=32, null=True)
    password_date = models.DateTimeField(default=timezone.now)
    disabled = models.BooleanField(default=False)
    expired = models.BooleanField(default=False)
    access_window_start = models.TimeField(null=True)
    access_window_end = models.TimeField(null=True)
    valid_from = models.DateField(null=True)
    valid_until = models.DateField(null=True)
    timezone = models.CharField(max_length=64, null=True)
    objects = GuacamoleManager()

    class Meta:
        db_table = 'guacamole_user'
        managed = False


# 连接共享配置
class GuacamoleSharingProfile(models.Model):
    sharing_profile_id = models.AutoField(primary_key=True)
    sharing_profile_name = models.CharField(max_length=128)
    primary_connection = models.ForeignKey(GuacamoleConnection, on_delete=models.CASCADE)
    objects = GuacamoleManager()

    class Meta:
        unique_together = (('sharing_profile_name', 'primary_connection'), )
        db_table = 'guacamole_sharing_profile'
        managed = False


# 连接详细参数
class GuacamoleConnectionParameter(models.Model):
    connection = models.ForeignKey(GuacamoleConnection, on_delete=models.CASCADE)
    parameter_name = models.CharField(max_length=128)
    parameter_value = models.CharField(max_length=4096)
    objects = GuacamoleManager()

    class Meta:
        unique_together = (('connection', 'parameter_name'), )
        db_table = 'guacamole_connection_parameter'
        managed = False


# 连接共享配置参数
class GuacamoleSharingProfileParameter(models.Model):
    sharing_profile = models.ForeignKey(GuacamoleSharingProfile, on_delete=models.CASCADE)
    parameter_name = models.CharField(max_length=128)
    parameter_value = models.CharField(max_length=4096)
    objects = GuacamoleManager()

    class Meta:
        unique_together = (('sharing_profile', 'parameter_name'), )
        db_table = 'guacamole_sharing_profile_parameter'
        managed = False


# 用户管理的连接权限
class GuacamoleConnectionPermission(models.Model):
    user = models.ForeignKey(GuacamoleUser, on_delete=models.CASCADE)
    connection = models.ForeignKey(GuacamoleConnection, on_delete=models.CASCADE)
    Permission = Enum(
        READ='READ',
        UPDATE='UPDATE',
        DELETE='DELETE',
        ADMINISTER='ADMINISTER',
    )
    permission = models.CharField(max_length=32)
    objects = GuacamoleManager()

    class Meta:
        unique_together = (('user', 'connection', 'permission'), )
        db_table = 'guacamole_connection_permission'
        managed = False


# 用户管理的连接组权限
class GuacamoleConnectionGroupPermission(models.Model):
    user = models.ForeignKey(GuacamoleUser, on_delete=models.CASCADE)
    connection_group = models.ForeignKey(GuacamoleConnectionGroup, on_delete=models.CASCADE)
    Permission = Enum(
        READ='READ',
        UPDATE='UPDATE',
        DELETE='DELETE',
        ADMINISTER='ADMINISTER',
    )
    permission = models.CharField(max_length=32)
    objects = GuacamoleManager()

    class Meta:
        unique_together = (('user', 'connection_group', 'permission'), )
        db_table = 'guacamole_connection_group_permission'
        managed = False


# 连接共享配置权限
class GuacamoleSharingProfilePermission(models.Model):
    user = models.ForeignKey(GuacamoleUser, on_delete=models.CASCADE)
    sharing_profile = models.ForeignKey(GuacamoleSharingProfile, on_delete=models.CASCADE)
    Permission = Enum(
        READ='READ',
        UPDATE='UPDATE',
        DELETE='DELETE',
        ADMINISTER='ADMINISTER',
    )
    permission = models.CharField(max_length=32)
    objects = GuacamoleManager()

    class Meta:
        unique_together = (('user', 'sharing_profile', 'permission'), )
        db_table = 'guacamole_sharing_profile_permission'
        managed = False


# 项目暂未使用到
class GuacamoleSystemPermission(models.Model):
    user = models.ForeignKey(GuacamoleUser, on_delete=models.CASCADE)
    Permission = Enum(
        CREATE_CONNECTION='CREATE_CONNECTION',
        CREATE_CONNECTION_GROUP='CREATE_CONNECTION_GROUP',
        CREATE_SHARING_PROFILE='CREATE_SHARING_PROFILE',
        CREATE_USER='CREATE_USER',
        ADMINISTER='ADMINISTER',
    )
    permission = models.CharField(max_length=32)
    objects = GuacamoleManager()

    class Meta:
        unique_together = (('user', 'permission'), )
        db_table = 'guacamole_system_permission'
        managed = False


# 用户权限
class GuacamoleUserPermission(models.Model):
    user = models.ForeignKey(GuacamoleUser, on_delete=models.CASCADE, related_name="+")
    affected_user = models.ForeignKey(GuacamoleUser, on_delete=models.CASCADE, related_name="+")
    Permission = Enum(
        READ='READ',
        UPDATE='UPDATE',
        DELETE='DELETE',
        ADMINISTER='ADMINISTER',
    )
    permission = models.CharField(max_length=32)
    objects = GuacamoleManager()

    class Meta:
        unique_together = (('user', 'affected_user', 'permission'), )
        db_table = 'guacamole_user_permission'
        managed = False


# 项目暂未使用到, 用户连接历史记录
class GuacamoleConnectionHistory(models.Model):
    history_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(GuacamoleUser, on_delete=models.CASCADE, null=True)
    username = models.CharField(max_length=128)
    connection = models.ForeignKey(GuacamoleConnection, on_delete=models.CASCADE, null=True)
    connection_name = models.CharField(max_length=128)
    sharing_profile = models.ForeignKey(GuacamoleSharingProfile, on_delete=models.CASCADE, null=True)
    sharing_profile_name = models.CharField(max_length=128, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True)
    objects = GuacamoleManager()

    class Meta:
        db_table = 'guacamole_connection_history'
        managed = False


# 项目暂未使用到, 用户密码历史记录
class GuacamoleUserPasswordHistory(models.Model):
    password_history_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(GuacamoleUser, on_delete=models.CASCADE)
    password_hash = models.BinaryField(max_length=32)
    password_salt = models.BinaryField(max_length=32, null=True)
    password_date = models.DateTimeField()
    objects = GuacamoleManager()

    class Meta:
        db_table = 'guacamole_user_password_history'
        managed = False
