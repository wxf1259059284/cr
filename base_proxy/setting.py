# -*- coding: utf-8 -*-

# nginx配置中, tcp代理配置文件路径
NGX_CONF_PATH = '/usr/local/nginx/conf/tcp.d/'

# 重启nginx命令
NGX_REBOOT_CMD = '/usr/local/nginx/sbin/nginx -c /usr/local/nginx/conf/rc.conf -s reload'

# 启动nginx命令
NGX_START_CMD = '/usr/local/nginx/sbin/nginx -c /usr/local/nginx/conf/rc.conf'

# nginx代理随机端口选择范围
PROXY_START_PORT = 20000
PROXY_END_PORT = 30000
PROXY_IP = '127.0.0.1'

SWITCH = False
