# -*- coding: utf-8 -*-
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone

from base.utils.enum import Enum
from base.utils.models.manager import MManager


class MUserManager(MManager, UserManager):
    pass


class Organization(models.Model):
    name = models.CharField(max_length=100, default='')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, default=None)


class User(AbstractUser):
    logo = models.ImageField(upload_to='user_logo', default='')
    nickname = models.CharField(max_length=100, default='')
    name = models.CharField(max_length=100, default='')
    profile = models.TextField(default='')
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True)

    last_login_ip = models.CharField(max_length=100, null=True, default=None)

    Group = Enum(
        ADMIN=1,
        STAFF=2,
    )
    Status = Enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)
    extra = models.TextField(default='')

    objects = MUserManager({'status': Status.DELETE})
    original_objects = models.Manager()

    @property
    def rep_name(self):
        return self.name or self.username

    @property
    def group(self):
        if self.is_superuser:
            return None

        group = self.groups.first()
        if not group:
            return None

        return group.pk

    @property
    def is_admin(self):
        if self.is_superuser:
            return True

        return self.group == User.Group.ADMIN


class Owner(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')

    PublicMode = Enum(
        PRIVATE=0,
        INNER=1,
        OUTER=2,
    )
    public_mode = models.PositiveIntegerField(default=PublicMode.PRIVATE)
    public_operate = models.BooleanField(default=False)

    create_time = models.DateTimeField(default=timezone.now)
    modify_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')
    modify_time = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True
