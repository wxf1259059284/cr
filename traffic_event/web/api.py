import json

from rest_framework import exceptions, viewsets, status, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response

from base.utils.rest.decorators import request_data
from base.utils.rest.mixins import CacheModelMixin, PMixin
from base_traffic.utils.traffic_logger import TrafficLogFactory
from cr_scene.models import CrScene
from traffic_event.models import TrafficEvent
from traffic_event.web.error import error
from traffic_event.web.serializers import TrafficEventSerializer
import logging
cr_logger = logging.getLogger(__name__)


class AgentViewSet(CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = TrafficEvent.objects.all()
    serializer_class = TrafficEventSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        check_result = request.data
        if check_result and check_result.get("cr_event") != "":
            scene_id = int(check_result.get("cr_event"))
            logger = TrafficLogFactory(scene_id, __name__)
        else:
            logger = cr_logger

        if check_result.get("result") == '' or check_result.get("result") is None:
            return Response(status=status.HTTP_200_OK)

        try:
            result = json.loads(check_result.get("result"))
            alive = result.get("alive")
        except Exception as e:
            logger.error("Get traffic check result error:%s", e)
            raise exceptions.APIException(error.GET_TRAFFIC_RESULT_ERROR)

        traffic_event_id = check_result.get("machine_id", "")
        if traffic_event_id is None or len(traffic_event_id) == 0:
            return Response(status=status.HTTP_200_OK)
        else:
            traffic_event = TrafficEvent.objects.filter(id=traffic_event_id).first()
            if traffic_event is not None:
                if not alive:
                    if traffic_event.status != TrafficEvent.Status.NORMAL:
                        traffic_event.status = TrafficEvent.Status.NORMAL
                        traffic_event.save()

                run_status = "RUN" if alive else "DOWN"
                logger.info("TrafficEvent[%s] Status:[%s]", traffic_event.title, run_status)

        return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
@request_data()
def get_traffic_event_status(request):
    data = []
    if request.query_data.data.get('crscene_id'):
        crscene_id = int(request.query_data.data.get('crscene_id'))
    else:
        raise exceptions.ParseError(error.REQUIRED_FIELD)

    if CrScene.objects.filter(id=crscene_id).first():
        crscene = CrScene.objects.filter(id=crscene_id).first()
    else:
        raise exceptions.NotFound(error.TRAFFIC_EVENT_NOT_FOUND)

    if crscene.traffic_events.all().first() is None:
        data = []
    else:
        for traffic_event in crscene.traffic_events.all():
            row = {
                'id': traffic_event.id,
                'title': traffic_event.title,
                'status': traffic_event.status,
            }
            data.append(row)
    return Response(data)
