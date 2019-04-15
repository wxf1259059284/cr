from django.conf.urls import url

from . import api


viewsets = (
    api.OrganizationViewSet,
    api.UserViewSet,
)


apiurlpatterns = [
    url(r'^login/$', api.SessionViewSet.as_csrf_view({'post': 'create'}), name='login'),
]
