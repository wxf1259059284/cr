from __future__ import unicode_literals

from keystoneclient.v3 import client
from keystoneauth1.identity import v3
from keystoneauth1 import session

try:
    from base_cloud import app_settings
except Exception:
    pass


class Client(object):
    def __init__(self, **kwargs):
        auth = v3.Password(
                auth_url=kwargs.get("auth_url") or app_settings.OS_AUTH.get("auth_url"),
                username=kwargs.get("username") or app_settings.OS_AUTH.get("username"),
                password=kwargs.get("password") or app_settings.OS_AUTH.get("password"),
                project_name=kwargs.get("project_name") or app_settings.OS_AUTH.get("project_name"),
                user_domain_id=kwargs.get("user_domain_id") or app_settings.OS_AUTH.get("user_domain_id"),
                project_domain_id=kwargs.get("project_domain_id") or app_settings.OS_AUTH.get("project_domain_id")
        )
        sess = session.Session(auth=auth)
        self.ks_client = client.Client(session=sess)

    def user_list(self, **kwargs):
        return self.ks_client.users.list()

    def project_list(self):
        return self.ks_client.projects.list()

    def project_get(self, project_name):
        projects = self.project_list()
        for project in projects:
            if project.name == project_name:
                return project
        return None


if __name__ == "__main__":
    cli = Client(auth_url="http://controller:35357/v3/", username="admin",
                 password="ADMIN_PASS", project_name="admin",
                 user_domain_id="default", project_domain_id="default")
    users = cli.user_list()
