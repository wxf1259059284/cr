# -*- coding: utf-8 -*-
from base_cloud import app_settings

from .docker import Docker
from .vm import Vm
from .qos import Qos
from .image import Image
from .network import Network
from .router import Router
from .firewall import Firewall
from .volume import Volume


docker = Docker()
vm = Vm()
qos = Qos()
image = Image()
network = Network()
router = Router()
firewall = Firewall()
volume = Volume()


def get_external_net():
    return app_settings.COMPLEX_MISC['external_net']
