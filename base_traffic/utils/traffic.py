from rest_framework import exceptions

from base_mission.check_api.get_script_parameter import kwargs_conversion
from base_traffic.cms.api import SCRIPT_URL
from base_traffic.models import Traffic, BackgroundTraffic, IntelligentTraffic
from base_traffic.traffic.error import error
from cr.settings import DOWNLOAD_SERVER
from traffic_event.models import TrafficEvent
from base_scene.common.util.terminal import TerminalUtil
from cr_scene.utils import scene as scene_utils


def copy_traffic(pk):
    try:
        new_traffic = Traffic.objects.get(id=pk)
    except Exception:
        return None
    traffic_id = new_traffic.id
    new_traffic.pk = None
    new_traffic.parent = pk
    new_traffic.is_copy = True
    new_traffic.save()

    new_traffic_id = new_traffic.id
    if new_traffic.type == Traffic.Type.BACKGROUND:
        new_extra_traffic = BackgroundTraffic.objects.get(traffic_id=traffic_id)
    elif new_traffic.type == Traffic.Type.INTELLIGENT:
        new_extra_traffic = IntelligentTraffic.objects.get(traffic_id=traffic_id)
    else:
        return None

    new_extra_traffic.pk = new_traffic_id
    new_extra_traffic.save()

    return new_traffic


def get_traffic_script(obj):
    if obj.type == TrafficEvent.Type.INTELLIGENT:
        if obj.traffic.intelligent_traffic.suffix == IntelligentTraffic.Suffix.PY:
            script_path = SCRIPT_URL + obj.traffic.title + "." + "py"
        else:
            script_path = SCRIPT_URL + obj.traffic.title + "." + "sh"

    else:
        script_path = "base_traffic/utils/tcp_replay.py"

    return script_path


def traffic_params(obj):
    extra_params = {}
    if obj.type == TrafficEvent.Type.BACKGROUND:
        bg = obj.traffic.background_traffic
        try:
            file_url = DOWNLOAD_SERVER + bg.pcap_file.url
        except Exception:
            raise exceptions.NotFound(error.FIELDS_NOT_EXIST)
        extra_params['file_url'] = file_url
        if bg.loop or bg.loop == 0:
            extra_params['loop'] = bg.loop
        if bg.mbps:
            extra_params['mbps'] = bg.mbps
        if bg.multiplier:
            extra_params['multiplier'] = bg.multiplier
    else:
        if obj.parameter:
            extra_params.update(kwargs_conversion(obj.parameter))

    return extra_params


def get_terminal_info(scene_id, sub_id, net_sub_id):
    target_terminal = scene_utils.get_scene_terminal(scene_id, sub_id)
    if target_terminal:
        target_name = target_terminal.name
        target_info = TerminalUtil(target_terminal).get_net_config(net_sub_id)
        if target_info:
            target_ip = target_info.get("ip")
            target_mac = target_info.get("mac_addr")
        else:
            target_ip = None
            target_mac = None
    else:
        target_name = None
        target_ip = None
        target_mac = None

    return target_name, target_ip, target_mac
