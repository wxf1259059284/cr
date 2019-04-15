from traffic_event.models import TrafficEvent


def handle_event_status(event, messages, logger):
    _ret = {}
    if not messages:
        return _ret

    if messages.get('status') == 'down':
        _ret = {'status': 'down', 'msg': 'Connection Refused'}
        event.status = TrafficEvent.Status.ERROR
        event.error = "TGM Connection Refused!"
        logger.error("TrafficEvent[%s]: TGM Connection Refused!", event.title)

    elif messages.get('status') == 'ok':
        if event.type == TrafficEvent.Type.BACKGROUND:
            if messages.get('content'):
                _ret = messages.get('content')
                if _ret != "" and _ret.get('status') == 'ok':
                    event.status = TrafficEvent.Status.RUNNING
                    event.error = ""
                    event.pid = _ret.get('pid')
                    logger.info("TrafficEvent[%s]: run success", event.title)

                if _ret != "" and _ret.get('status') == 'error' and _ret.get('msg'):
                    event.status = TrafficEvent.Status.ERROR
                    event.error = _ret.get('msg')
                    event.pid = ''
                    logger.error("TrafficEvent[%s] running error: %s", event.title, _ret.get('msg'))

        else:
            event.status = TrafficEvent.Status.RUNNING
            if messages.get('pid'):
                parent_pid = int(messages.get('pid'))
                event.pid = parent_pid + 1

            if messages.get('content'):
                _ret = {'status': 'ok', 'msg': messages.get('content')}
            else:
                _ret = {'status': 'ok', 'msg': 'script run success'}
            event.error = ""
            logger.info("TrafficEvent[%s]: is running", event.title)

    else:
        event.status = TrafficEvent.Status.ERROR
        error_msg = messages.get('content') if messages.get('content') else 'unknown error'
        event.error = error_msg
        _ret = {'status': 'error', 'msg': error_msg}
        logger.error("TrafficEvent[%s] running error: %s", event.title, error_msg)

    event.save()
    return _ret, event
