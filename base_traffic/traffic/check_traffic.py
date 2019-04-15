import json


def start_check_traffic(ac, traffic_event, scene_id, logger):
    if not traffic_event.pid:
        logger.info("TrafficEvent[%s]: Can not get pid,reset to default after 30s ", traffic_event.title)
        pid = 999999
        delay_time = 30
    else:
        pid = int(traffic_event.pid)
        delay_time = 2

    parameter = {'pid': pid}
    ac.scheduler_execute_script(
        "base_traffic/utils/check_process.py",
        main_func="check_process",
        scene_id=str(scene_id),
        parameter_id=str(traffic_event.id),
        script_args=json.dumps(parameter),
        trigger_args=json.dumps({
            "delay":  delay_time,
            "seconds": 10,
        }),
        report_url="http://169.254.169.254/cr/api/traffic_event/agents/"
    )
