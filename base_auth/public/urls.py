from django.conf.urls import url

from . import rest_views


apiurlpatterns = [
    url(r'^logout/$', rest_views.logout, name='logout'),
    url(r'^user/info/$', rest_views.user_info, name='user_info'),
]
