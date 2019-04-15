
import re

from channels.routing import include


def get_default_router(websocket_classes):
    routers = []
    for websocket_class in websocket_classes:
        names = re.findall(r'[A-Z][a-z]+', websocket_class.__name__)
        names = [s.lower() for s in names[:-1]]
        name = '_'.join(names)
        path = '/{}'.format(name)
        routers.append(websocket_class.as_new_route(path))
    return routers


def ws_path(websocket_classes):
    routers = get_default_router(websocket_classes)
    return include(routers)
