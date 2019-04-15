# -*- coding: utf-8 -*-
from django.conf.urls import url

from dashboard.cms import views


apiurlpatterns = [
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^get_system_state/$', views.get_system_state, name='get_system_state'),
    url(r'^get_system_used/$', views.get_system_used, name='get_system_used'),
]
