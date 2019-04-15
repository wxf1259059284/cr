from __future__ import unicode_literals

import docker

try:
    from base_cloud.setting import api_settings
except Exception:
    pass


DEFAULT_CA_PATH = "/etc/docker/ssl/ca.pem"
DEFAULT_CLIENT_KEY_PATH = "/etc/docker/ssl/key.pem"
DEFAULT_CLIENT_CERT_PATH = "/etc/docker/ssl/cert.pem"


class DockerHTTPClient(docker.APIClient):
    def __init__(self, base_url, ca_cert=None,
                 client_key=None, client_cert=None):

        if ca_cert and client_key and client_cert:
            ssl_config = docker.tls.TLSConfig(
                client_cert=(client_cert, client_key),
                ca_cert=ca_cert,
                assert_hostname=False,
            )
        else:
            ssl_config = False

        super(DockerHTTPClient, self).__init__(
            base_url=base_url,
            tls=ssl_config
        )


class Client(object):
    def __init__(self, **kwargs):
        self.cli = DockerHTTPClient(
            base_url=kwargs.get("base_url") or api_settings.COMPLEX_MISC.get("base_url"),
            ca_cert=api_settings.COMPLEX_MISC.get("ca_cert") or DEFAULT_CA_PATH,
            client_key=api_settings.COMPLEX_MISC.get("client_key") or DEFAULT_CLIENT_KEY_PATH,
            client_cert=api_settings.COMPLEX_MISC.get("client_cert") or DEFAULT_CLIENT_CERT_PATH)

    def import_image_from_file(self, filename, repository=None, tag=None,
                               changes=None):
        return self.cli.import_image_from_file(filename, repository, tag, changes)

    def load_image(self, image_path=None):
        if image_path:
            with open(image_path, 'rb') as fd:
                self.cli.load_image(fd)

    def inspect_image(self, image):
        return self.cli.inspect_image(image)

    def get_image(self, image):
        return self.cli.get_image(image)

    def list_images(self, name=None, quiet=False, all=False, viz=False, filters=None):
        return self.cli.images(name, quiet, all, viz, filters)

    def remove_image(self, image, force=False, noprune=False):
        self.cli.remove_image(image, force, noprune)

    def prune_images(self, filters=None):
        self.cli.prune_images(filters)

    def tag_image(self, image, repository, tag=None, force=False):
        self.cli.tag(image, repository, tag, force)

    def commit_container(self, container, repository=None, tag=None,
                         message=None, author=None, changes=None, conf=None):
        self.cli.commit(container, repository, tag, message,
                        author, changes, conf)

    def prune_containers(self, filters=None):
        self.cli.prune_containers(filters)

    def remove_container(self, container, v=False, link=False, force=False):
        self.cli.remove_container(container, v, link, force)

    def rename_container(self, container, name):
        self.cli.remove_container(container, name)

    def restart_container(self, container, timeout=10):
        self.cli.restart(container, timeout)

    def list_containers(self, filters=None):
        return self.cli.containers(all=True, filters=filters)

    def prune_networks(self, filters=None):
        if not filters:
            filters = {}
        return self.cli.prune_networks(filters=filters)

    def list_networks(self, names=None, ids=None, filters=None):
        if not filters:
            filters = {}
        filters.update({"driver": "kuryr"})
        return self.cli.networks(names=names, ids=ids, filters=filters)

    def inspect_network(self, net_id):
        return self.cli.inspect_network(net_id)

    def remove_network(self, net_id):
        return self.cli.remove_network(net_id)

    def create_network(self, name, driver=None, options=None, ipam=None,
                       check_duplicate=None, internal=False, labels=None,
                       enable_ipv6=False, attachable=None, scope=None,
                       ingress=None):
        return self.cli.create_network(name, driver=driver, options=options,
                                       ipam=ipam, check_duplicate=check_duplicate,
                                       internal=internal, labels=labels,
                                       enable_ipv6=enable_ipv6, attachable=attachable,
                                       scope=scope, ingress=ingress)


if __name__ == "__main__":
    cli = Client(base_url='tcp://controller:2375',
                 ca_cert="/home/moose/ssl/ca.pem",
                 client_key="/home/moose/ssl/server-key.pem",
                 client_cert="/home/moose/ssl/server-cert.pem")
    try:
        nets = cli.list_networks()
    except Exception as e:
        pass
