from base_scene.common.util.terminal import TerminalUtil
from cr_scene.utils import scene as scene_utils


def get_checker_ip(scene_id, sub_id):
    scene = scene_utils.get_scene(scene_id)
    if scene is None:
        return None, None

    parameter = scene_utils.get_terminal_access_infos(
        scene, sub_id,
    )
    if parameter and parameter[0]:
        return parameter[0][1], parameter[0][2]
    else:
        return None, None


def get_terminal_ip(scene_id, sub_id, net_sub_id):
    target_terminal = scene_utils.get_scene_terminal(scene_id, sub_id)
    if target_terminal:
        target_info = TerminalUtil(target_terminal).get_net_config(net_sub_id)
        if target_info:
            target_ip = target_info.get("ip")
        else:
            target_ip = None
    else:
        target_ip = None

    return target_ip
