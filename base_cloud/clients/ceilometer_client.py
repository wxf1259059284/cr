from __future__ import unicode_literals
import re

from ceilometerclient import client

try:
    from base_cloud import app_settings
except Exception:
    pass


class Statistic(object):
    _attrs = ['period', 'period_start', 'period_end',
              'count', 'min', 'max', 'sum', 'avg',
              'duration', 'duration_start', 'duration_end', 'unit']
    _statistic = None

    def __init__(self, statistic):
        self._statistic = statistic

    def to_dict(self):
        obj = {}
        for key in self._attrs:
            obj[key] = getattr(self._statistic, key, None)
        return obj


class Sample(object):
    _attrs = ['counter_name', 'user_id', 'resource_id', 'timestamp',
              'resource_metadata', 'source', 'counter_unit', 'counter_volume',
              'project_id', 'counter_type', 'resource_metadata']
    _sample = None

    def __init__(self, sample):
        self._sample = sample

    def to_dict(self):
        obj = {}
        for key in self._attrs:
            obj[key] = getattr(self._sample, key, None)
        return obj


class Client(object):
    def __init__(self):
        self.ceil_client = client.get_client(
            "2",
            os_username=app_settings.OS_AUTH.get("username"),
            os_password=app_settings.OS_AUTH.get("password"),
            os_tenant_name=app_settings.OS_AUTH.get("project_name"),
            os_auth_url=app_settings.OS_AUTH.get("auth_url")
        )

    def meter_list(self):
        return self.ceil_client.meters.list()

    def resource_list(self, query=None):
        return self.ceil_client.resources.list(q=query)

    def get_vifs_resource(self, inst_id):
        patten = re.compile(r"instance-.*-{}-tap.*".format(inst_id))
        resources = self.resource_list()
        return [r for r in resources if patten.match(r.id)]

    def statistic_list(self, meter_name, query=None, period=None):
        stats = self.ceil_client.statistics.list(meter_name=meter_name,
                                                 q=query,
                                                 period=period)
        return [Statistic(stat).to_dict() for stat in stats]

    def sample_list(self, meter_name, query=None, limit=None):
        """List the samples for this meters."""
        samples = self.ceil_client.samples.list(meter_name=meter_name,
                                                q=query, limit=limit)
        return [Sample(s).to_dict() for s in samples]
