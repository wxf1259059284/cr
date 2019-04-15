## 打包命令

### Linux:

```
# pyupdater build --console --add-data="agent.thrift:." --add-data="thriftpy.transport.cybase.so:." --app-version 0.0.1 server.py

# pyupdater pkg --process --sign
```


###　Windows:

```
> pyupdater build --console --add-data="agent.thrift;." -i favicon.ico --noconsole --app-version 0.0.1 server.py

> pyupdater pkg --process --sign
```

## 安装

### Linux：

```
1. 下载安装包
# wget http://169.254.169.254/cr/media/rpc_framework/cragentserver-nix64-0.0.1.tar.gz

2. 解压并拷贝
# tar xvf cragentserver-nix64-0.0.1.tar.gz
# mv cragentserver /usr/local/
```

### Windows:

```
1. 下载安装包: 
[http://169.254.169.254/cr/media/rpc_framework/cragentserver-win-0.0.1.zip](http://169.254.169.254/cr/media/rpc_framework/cragentserver-win-0.0.1.zip)

2. 解压到c盘根目录：
C:\cragentserver
```

## 开机启动

### Centos

```
# vim /usr/lib/systemd/system/njcr-agent-server.service
```

```
[Unit]
Description=NJCR Agent Server
After=syslog.target network.target

[Service]
ExecStart = /usr/local/cragentserver/cragentserver
User = root
Restart=on-failure
TimeoutStartSec=0
WorkingDirectory=/usr/local/

[Install]
WantedBy=multi-user.target

```

```
# systectl daemon-reload
# systemctl enable njcr-agent-server
```

### Ubuntu

```bash
# vim /etc/systemd/system/njcr-agent-server.service
```

```
[Unit]
Description=NJCR Agent Server
After=syslog.target network.target

[Service]
ExecStart = /usr/local/cragentserver/cragentserver
User = root
Restart=on-failure
TimeoutStartSec=0
WorkingDirectory=/usr/local/

[Install]
WantedBy=multi-user.target
```

```
# systectl daemon-reload
# systemctl enable njcr-agent-server
```

### linux

```
# vim /etc/rc.local
(cd /usr/local/ && ./cragentserver/cragentserver &)
```


### windows

```
创建桌面快捷方式，将快捷方式加入到开始菜单的启动目录中
```
