from __future__ import unicode_literals

import datetime
import functools
import logging

from django.utils.translation import ugettext as _

from base_cloud.clients.ceilometer_client import Client as celi_client
from base_cloud.exception import FriendlyException


METERS = {
    'cpu_usage': "cpu_util",
    'mem_total': "memory",
    'mem_used': "memory.usage",
    'disk_used': "disk.allocation",
    'disk_total': "disk.capacity",
    'disk_io_r': "disk.read.bytes.rate",
    'disk_io_w': "disk.write.bytes.rate",
    'disk_iops_r': "disk.read.requests.rate",
    'disk_iops_w': "disk.write.requests.rate"
}
NET_METERS = {
    'net_in_pkts': "network.incoming.packets",
    'net_out_pkts': "network.outgoing.packets",
    'net_in_bytes': "network.incoming.bytes",
    'net_out_bytes': "network.outgoing.bytes",
}
# second
PERIOD = 60
# minutes
DURATION = 1
INTERVAL = 30
TIME_FORMAT = "%Y-%m-%dT%H%M%S"
LOG = logging.getLogger(__name__)


def logger_decorator(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        func_name = func.__name__
        LOG.debug("Start {}(): args={}, kwargs={}".format(func_name,
                                                          args, kwargs))
        ff = func(self, *args, **kwargs)
        LOG.debug("End {}()".format(func_name))
        return ff
    return wrapper


class MeterAction(object):
    def __init__(self):
        self.ceilometer_client = celi_client()

    def _handle_error(self, err_msg=None, e=None):
        if not err_msg:
            err_msg = _("Unknown error occurred, Please try again later.")
        if e:
            err_msg = "{}\n{}".format(err_msg, getattr(e, "message", ""))
        LOG.error(err_msg)
        raise FriendlyException(err_msg)

    @logger_decorator
    def statistic_list(self, resource_id):
        if not resource_id:
            err_msg = _("Params not legal. resource_id "
                        "must be configured.")
            self._handle_error(err_msg)

        duration_start = (datetime.datetime.utcnow() -
                          datetime.timedelta(minutes=DURATION)).strftime(TIME_FORMAT)
        statistics = {}
        q = [{"field": "timestamp",
              "op": "ge",
              "value": duration_start},
             {"field": "resource_id",
              "op": "eq",
              "value": resource_id}]

        # get memory cpu disk data
        for meter_key, meter_value in METERS.items():
            try:
                statistics[meter_key] = self.ceilometer_client.statistic_list(meter_value, q)[0]
            except Exception as e:
                err_msg = _("Unable to get statistics {}.").format(meter_key)
                LOG.error(err_msg)
                LOG.error(e)
                statistics[meter_key] = None

        # if can not get memory total data
        if not statistics['mem_total']:
            statistics['mem_total'] = {'avg': 0, 'unit': None}
            q = [{"field": "resource_id",
                  "op": "eq",
                  "value": resource_id}]
            samples = self.ceilometer_client.sample_list('memory', q, 1)
            if samples:
                statistics['mem_total']['avg'] = samples[0].get('counter_volume')
                statistics['mem_total']['unit'] = samples[0].get('counter_unit')

        # get interface data
        vifs = self.ceilometer_client.get_vifs_resource(resource_id)
        for vif in vifs:
            q = [{"field": "resource_id",
                  "op": "eq",
                  "value": vif.resource_id}]
            for net_meter_key, net_meter_val in NET_METERS.items():
                meter_rate = "{}{}".format(net_meter_key, "_rate")
                if meter_rate not in statistics.keys():
                    statistics[meter_rate] = {'avg': 0, 'unit': None}
                try:
                    samples = self.ceilometer_client.sample_list(net_meter_val, q, 2)
                    if not samples:
                        continue
                    if not statistics[meter_rate].get("unit"):
                        statistics[meter_rate]['unit'] = "{}{}".format(samples[0].get('counter_unit'), "/s")
                    if len(samples) == 2:
                        rate = (samples[0].get('counter_volume') - samples[1].get('counter_volume')) / INTERVAL
                        statistics[meter_rate]['avg'] += rate if rate > 0 else 0
                    if len(samples) == 1:
                        statistics[meter_rate]['avg'] += samples[0]
                except Exception as e:
                    err_msg = _("Unable to get statistics {}.").format(net_meter_key)
                    LOG.error(err_msg)
                    LOG.error(e)

        return statistics
