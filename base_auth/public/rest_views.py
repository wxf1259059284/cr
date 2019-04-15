from django.contrib.auth import logout as django_logout

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from base_auth.web.serializers import UserSerializer


@api_view(['GET', 'POST'])
@permission_classes((permissions.AllowAny,))
def logout(request):
    django_logout(request)
    return Response(status=status.HTTP_200_OK)


@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated,))
def user_info(request):
    user = request.user
    data = UserSerializer(user).data
    return Response(data=data, status=status.HTTP_200_OK)
