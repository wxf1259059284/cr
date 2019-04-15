# -*- coding: utf-8 -*-
from . import consumers

websockets = (
    consumers.CheckReportWebsocket,
    consumers.EvaluationReportWebsocket,
)

routerpatterns = []
