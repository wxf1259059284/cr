# -*- coding: utf-8 -*
import os
import re
import urllib
import uuid
import time
import threading
import datetime

import netifaces
import subprocess


# netifaces:https://pypi.org/project/netifaces/
# tcprewrite:http://tcpreplay.synfin.net/wiki/usage#01
LOCAL_PATH = "/tmp/"


class TcpReplay(object):
    def __init__(self, url, dst_ip, dst_mac, loop, multiplier, mbps):
        self.interface, self.ip, self.mac = self.get_interface_info()
        self.path = self.handle_file(url)
        self.dst_ip = dst_ip
        self.dst_mac = dst_mac
        self.loop = loop
        self.multiplier = multiplier
        self.mbps = mbps

    @staticmethod
    def get_interface_info():
        gws = netifaces.gateways()
        if gws['default']:
            interface = gws['default'][netifaces.AF_INET][1]
            ip = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
            mac = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
        else:
            interface = None
            ip = None
            mac = None

        return interface, ip, mac

    @staticmethod
    def handle_file(url):
        file_name = url.split("/")[-1]
        random_str = str(uuid.uuid4()).upper()[0:7]
        file_path = LOCAL_PATH + file_name.split(".")[0] + "_" + random_str + "." + file_name.split(".")[-1]
        try:
            urllib.urlretrieve(url, file_path)
        finally:
            if os.path.exists(file_path):
                return file_path
            else:
                return None

    def get_pid(self, hash_file):
        command = "ps -ef|grep %s" % hash_file
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        res_f = process.stdout
        if res_f:
            lines = res_f.readlines()
            number_group = re.search(r'root\s+?(\d+)', lines[1])
            pid = number_group.group(1)
        else:
            pid = None
        return pid

    def execute_command(self, command):
        dir_path = os.path.dirname(self.path)
        log_path = os.path.join(dir_path, 'tcpreplay_log.log')
        print(command)
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        res_f = process.stdout
        lines = res_f.readlines()
        if lines:
            with open(log_path, 'a+') as f:
                f.write('----------%s---------- \n' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                for line in lines:
                    f.write(line)

    def execute_command_async(self, command):
        _thread = threading.Thread(target=self.execute_command, args=(command,))
        _thread.start()

    def execute_replay(self):
        _ret = {'status': 'error', 'msg': '', 'pid': ''}
        extra_params = ""

        if not self.path:
            _ret['msg'] = 'pcap file download error'
            return _ret

        if not self.interface:
            _ret['msg'] = 'get network interface error'
            return _ret

        if not self.dst_ip or not self.dst_mac:
            _ret['msg'] = 'traffic args error'
            return _ret

        ip_map = "--srcipmap=0.0.0.0/0:%s/32 --dstipmap=0.0.0.0/0:%s/32" % (self.ip, self.dst_ip)
        net_mac = "--enet-smac=%s --enet-dmac=%s" % (self.mac, self.dst_mac)
        outfile_path = os.path.splitext(self.path)[0] + '_rewrite.pcap'
        command_rewrite = "tcprewrite --fixcsum %s %s --infile=%s --outfile=%s" % (
            ip_map, net_mac, self.path, outfile_path)
        self.execute_command(command_rewrite)

        if self.loop or self.loop == 0:
            extra_params += " --loop=%s" % self.loop
        if self.multiplier:
            extra_params += " --multiplier=%s" % self.multiplier
        if self.mbps:
            extra_params += " --mbps=%s" % self.mbps

        command_replay = "tcpreplay %s --intf1=%s %s" % (extra_params, self.interface, outfile_path)
        self.execute_command_async(command_replay)
        time.sleep(0.2)
        pid = self.get_pid(outfile_path)
        _ret = {'status': 'ok', 'msg': 'tcpreplay running', 'pid': '%s' % pid}

        return _ret


def traffic(dst_ip=None, dst_mac=None, file_url=None, loop=None, multiplier=None, mbps=None):
    try:
        tcp_replay = TcpReplay(file_url, dst_ip, dst_mac, loop, multiplier, mbps)
        _ret = tcp_replay.execute_replay()
    except Exception:
        _ret = {'status': 'error', 'msg': 'script run error', 'pid': ''}

    return _ret


# if __name__ == '__main__':
#     traffic('192.168.200.8', 'fa:16:3e:81:23:0a', 'http://192.168.100.156/media/traffic/pcap/wechat.pcap', '1', '1.5')
