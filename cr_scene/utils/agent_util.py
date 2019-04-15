import json
import logging
import os

from django.conf import settings

from base.utils.rpc import client as rpc_client
from cr_scene.utils.scene import get_terminal_access_infos, get_terminal_util

logger = logging.getLogger(__name__)


SYS_INFO_SCRIPT = os.path.join(settings.BASE_DIR, "media/scripts/sys_info.py")
# SYS_INFO_SCRIPT = "http://169.254.169.254/cr/media/scripts/sys_info.py"


def report_sys_info(scene_id, machine_id):
    term = get_terminal_util(terminal_id=machine_id)
    if term.standard_device and term.standard_device.type == 0:
        infos = get_terminal_access_infos(terminal_util=term, filters={"port": 8192})
        logger.info("Get infos: {}".format(infos))
        if not infos:
            return False
        if len(infos[0]) == 3:
            proxy_type, proxy_host, proxy_port = infos[0]
        elif len(infos[0]) == 4:
            proxy_type, proxy_host, proxy_port, dest_port = infos[0]
        else:
            return False
        logger.info("Script path: {}".format(SYS_INFO_SCRIPT))
        cli = rpc_client.AgentClient(host=proxy_host, port=proxy_port)
        cli.scheduler_execute_script(file_path=SYS_INFO_SCRIPT,
                                     scene_id=str(scene_id),
                                     parameter_id=str(machine_id),
                                     main_func="main",
                                     trigger_args=json.dumps({"seconds": 120}))
