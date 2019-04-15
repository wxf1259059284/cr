# 标靶

## 标靶 StandardDevice

| 字段                   | 类型     | 说明                             | 是否必须 | 默认值   | 限制                                               |
| ---------------------- | -------- | -------------------------------- | -------- | -------- | -------------------------------------------------- |
| name                   | string   | 名称                             | 是       |          | 不可重复，不可包含空格和特殊字符                   |
| description            | string   | 说明                             | 否       | 空       |                                                    |
| logo                   | string   | 图标，自定义上传或使用默认字图标 | 是       |          |                                                    |
| role                   | integer  | 角色                             | 是       |          | 1-网络  2-网关  3-终端                             |
| role_type              | integer  | 角色类型，对应角色有对应的类型   | 是       |          | 见备注                                             |
| is_real                | boolean  | 是否是实体设备                   | 否       | false    | 默认虚拟设备                                       |
| wan_number             | integer  | 虚拟网关wan口数量                | 否       | 0        |                                                    |
| lan_number             | integer  | 虚拟网关lan口数量                | 否       | 0        |                                                    |
| lan_configs            | string   | 虚拟网关lan口配置                | 否       | '[]'     |                                                    |
| image_type             | string   | 镜像类型                         | 否       | null     | vm-虚拟机 <br />docker-容器                        |
| system_type            | string   | 系统类型                         | 否       | null     | linux<br />windows<br />other                      |
| system_sub_type        | string   | 详细系统类型                     | 否       | other    | 见备注                                             |
| flavor                 | string   | 镜像大小                         | 否       | null     | 见备注                                             |
| source_image_name      | string   | 源镜像名称                       | 否       | null     |                                                    |
| disk_format            | string   | 磁盘格式                         | 否       | null     |                                                    |
| meta_data              | string   | 元数据                           | 否       | null     |                                                    |
| access_mode            | string   | 接入协议                         | 否       | null     |                                                    |
| access_port            | string   | 接入端口                         | 否       | null     |                                                    |
| access_connection_mode | string   | rdp访问模式                      | 否       | null     | rdp/nla                                            |
| access_user            | string   | 接入用户                         | 否       | null     |                                                    |
| access_password        | string   | 接入密码                         | 否       | null     |                                                    |
| init_support           | boolean  | 是否支持初始化                   | 否       | false    |                                                    |
| image_status           | integer  | 镜像状态                         | 否       | 0        | 0-待编辑<br />1-创建中<br />2-创建完成<br />3-错误 |
| error                  | string   | 错误信息                         | 否       | null     |                                                    |
| tmp_vm                 | integer  | 镜像机器                         | 否       | null     |                                                    |
| hash                   | string   | 记录hash，随机生成               | 否       | 随机生成 |                                                    |
| status                 | integer  | 记录状态                         | 否       | 1        | 0-已删除<br />1-正常                               |
| create_time            | datetime | 创建时间                         | 否       | 当前时间 |                                                    |
| create_user            | integer  | 创建用户                         | 否       | 当前用户 |                                                    |
| modify_time            | datetime | 修改时间                         | 否       | 当前时间 |                                                    |
| modify_user            | integer  | 修改用户                         | 否       | null     |                                                    |

### 备注**：

| role | role_type | 说明               |
| ---- | --------- | ------------------ |
| 1    | 1         | 网络               |
| 2    | 1         | 简易路由           |
| 2    | 2         | 简易防火墙         |
| 2    | 3         | 虚拟路由           |
| 2    | 4         | 虚拟防火墙         |
| 2    | 5         | WAF                |
| 2    | 6         | IPS                |
| 2    | 7         | IDS                |
| 2    | -1        | 【实体】远程地址型 |
| 2    | -2        | 【实体】设备端口型 |
| 2    | -3        | 【实体】无线型     |
| 3    | 1         | Web服务器          |
| 3    | 2         | 数据库服务器       |
| 3    | 3         | 文件服务器         |
| 3    | 4         | 二进制服务器       |
| 3    | 5         | 邮件服务器         |
| 3    | 6         | 办公设备           |
| 3    | 7         | 移动设备           |
| 3    | 8         | 工控设备           |
| 3    | 9         | 智能设备           |
| 3    | 10        | UAV                |
| 3    | 0         | 其他               |
| 3    | -1        | 【实体】远程地址型 |
| 3    | -2        | 【实体】设备端口型 |
| 3    | -3        | 【实体】无线型     |

| system_sub_type     |
| ------------------- |
| kali-2              |
| ubuntu-12           |
| ubuntu-14           |
| ubuntu-15           |
| centos-7            |
| centos-6            |
| centos-5            |
| windows-xp          |
| windows-7           |
| windows-8           |
| windows-10          |
| windows-server-2012 |
| windows-server-2008 |
| windows-server-2003 |
| windows-server-2000 |
| android             |
| ubuntukylin-18      |
| opensolaris-11      |
| opensuse-leap-42    |
| debian-9            |
| deepofix            |
| redhat-7            |
| backtrack-5         |
| other               |

| flavor         | 说明                 |
| -------------- | -------------------- |
| m1.1c-0.5g-8g  | 1核/512M内存/8G硬盘  |
| m1.1c-1g-8g    | 1核/1G内存/8G硬盘    |
| m2.1c-0.5g-10g | 1核/512M内存/10G硬盘 |
| m2.1c-1g-10g   | 1核/1G内存/10G硬盘   |
| m2.2c-2g-10g   | 2核/2G内存/10G硬盘   |
| m2.2c-4g-10g   | 2核/3G内存/10G硬盘   |
| m3.1c-1g-20g   | 1核/1G内存/20G硬盘   |
| m3.1c-2g-20g   | 1核/2G内存/20G硬盘   |
| m3.2c-4g-20g   | 2核/4G内存/20G硬盘   |
| m3.4c-4g-20g   | 4核/4G内存/20G硬盘   |
| m4.1c-1g-40g   | 1核/1G内存/40G硬盘   |
| m4.2c-2g-40g   | 2核/2G内存/40G硬盘   |
| m4.4c-4g-40g   | 4核/4G内存/40G硬盘   |
| m4.4c-8g-40g   | 4核/8G内存/40G硬盘   |
| m5.4c-4g-80g   | 4核/4G内存/80G硬盘   |
| m5.4c-8g-80g   | 4核/8G内存/80G硬盘   |

## 标靶快照 StandardDeviceSnapshot

| 字段            | 类型     | 说明               | 是否必须 | 默认值   | 限制 |
| --------------- | -------- | ------------------ | -------- | -------- | ---- |
| standard_device | integer  | 所属标靶，外键标靶 | 是       |          |      |
| name            | string   | 快照名称           | 是       |          |      |
| desc            | string   | 快照描述           | 是       |          |      |
| create_time     | datetime | 创建时间           | 否       | 当前时间 |      |



# 场景模型设计

## 场景配置 SceneConfig

| 字段        | 类型    | 说明     | 是否必须 | 默认值 | 限制       |
| ----------- | ------- | -------- | -------- | ------ | ---------- |
| type        | integer | 场景类型 | 否       | 1      | 1-基础场景 |
| file        | string  | 场景文件 | 否       | null   |            |
| json_config | string  | 场景配置 | 是       | {}     |            |
| name        | string  | 场景名称 | 否       | null   |            |

## 活动场景实例 Scene

| 字段           | 类型     | 说明                   | 是否必须 | 默认值   | 限制                                                         |
| -------------- | -------- | ---------------------- | -------- | -------- | ------------------------------------------------------------ |
| user           | integer  | 创建用户，外键用户     | 是       |          |                                                              |
| type           | integer  | 场景类型               | 否       | 1        | 1-基础场景                                                   |
| file           | string   | 场景文件               | 否       |          |                                                              |
| json_config    | string   | 场景配置               | 是       | null     |                                                              |
| hang_info      | string   | 被外部引用的关系       | 否       | {}       |                                                              |
| name_prefix    | string   | 资源名称前缀           | 否       | 空       |                                                              |
| status         | integer  | 场景状态               | 是       | 1        | 0-已删除<br />1-创建中<br />2-运行中<br />3-暂停中<br />4-错误 |
| status_updated | integer  | 状态更新回调，外键任务 | 否       | null     |                                                              |
| log            | string   | 记录场景创建流程日志   | 否       | []       |                                                              |
| error          | string   | 记录场景出错信息       | 否       | null     |                                                              |
| create_time    | datetime | 创建时间               | 是       | 当前时间 |                                                              |
| created_time   | datetime | 完成时间               | 否       | null     |                                                              |
| consume_time   | integer  | 消耗时间               | 否       | 0        |                                                              |
| pause_time     | datetime | 暂停时间               | 否       | null     |                                                              |

## 活动场景实例网络 SceneNet

| 字段            | 类型    | 说明                             | 是否必须 | 默认值 | 限制       |
| --------------- | ------- | -------------------------------- | -------- | ------ | ---------- |
| scene           | integer | 外键所属场景                     | 是       |        |            |
| sub_id          | string  | 场景内id                         | 是       |        |            |
| name            | string  | 名称                             | 是       |        |            |
| is_real         | boolean | 是否实体设备                     | 否       | false  |            |
| visible         | boolean | 是否可见                         | 否       | true   |            |
| type            | integer | 网络类型，同标靶网络对应角色类型 | 否       | 1      | 见标靶备注 |
| image           | string  | 对应标靶                         | 否       | 空     |            |
| cidr            | string  | 网段                             | 否       | null   |            |
| gateway         | string  | 网关                             | 否       | null   |            |
| dns             | string  | dns                              | 否       | null   |            |
| dhcp            | boolean | 是否开启dhcp                     | 否       | true   |            |
| net_id          | string  | 网络id                           | 否       | null   |            |
| subnet_id       | string  | 子网id                           | 否       | null   |            |
| vlan_id         | string  | vlan id                          | 否       | null   |            |
| vlan_info       | string  | vlan信息                         | 否       | 空     |            |
| proxy_router_id | string  | 本地代理路由id                   | 否       | null   |            |

## 活动场景实例网关 SceneGateway

| 字段               | 类型     | 说明                             | 是否必须 | 默认值 | 限制       |
| ------------------ | -------- | -------------------------------- | -------- | ------ | ---------- |
| scene              | integer  | 外键所属场景                     | 是       |        |            |
| sub_id             | string   | 场景内id                         | 是       |        |            |
| name               | string   | 名称                             | 是       |        |            |
| is_real            | boolean  | 是否实体设备                     | 否       | false  |            |
| visible            | boolean  | 是否可见                         | 否       | true   |            |
| type               | integer  | 网关类型，同标靶网关对应角色类型 | 否       | 1      | 见标靶备注 |
| image              | string   | 对应标靶                         | 否       | 空     |            |
| nets               | relation | 连接的网络，多对多关系           | 否       |        |            |
| router_id          | string   | 路由id                           | 否       | null   |            |
| static_routing     | string   | 静态路由                         | 否       | 空     |            |
| firewall_rule      | string   | 防火墙规则                       | 否       | 空     |            |
| firewall_id        | string   | 防火墙id                         | 否       | null   |            |
| can_user_configure | boolean  | 是否允许用户修改                 | 否       | false  |            |

## 活动场景实例终端 SceneTerminal

| 字段             | 类型     | 说明                                   | 是否必须 | 默认值   | 限制                                                         |
| ---------------- | -------- | -------------------------------------- | -------- | -------- | ------------------------------------------------------------ |
| scene            | integer  | 外键所属场景                           | 是       |          |                                                              |
| sub_id           | string   | 场景内id                               | 是       |          |                                                              |
| name             | string   | 名称                                   | 是       |          |                                                              |
| is_real          | boolean  | 是否实体设备                           | 否       | false    |                                                              |
| visible          | boolean  | 是否可见                               | 否       | true     |                                                              |
| type             | integer  | 终端类型，同标靶终端对应角色类型       | 否       | 1        | 见标靶备注                                                   |
| image            | string   | 对应标靶                               | 否       | 空       |                                                              |
| nets             | relation | 连接的网络，多对多关系                 | 否       |          |                                                              |
| system_type      | string   | 系统类型，同标靶对应系统类型           | 否       | linux    | 见标靶                                                       |
| system_sub_type  | string   | 详细系统类型，同标靶对应详细系统类型   | 否       | other    | 见标靶                                                       |
| image_type       | string   | 镜像类型，同标靶对应镜像类型           | 否       | vm       | 见标靶                                                       |
| role             | string   | 角色                                   | 否       | target   | operator-操作机<br />target-靶机<br />wingman-僚机<br />gateway-网关<br />executer-执行机 |
| flavor           | string   | 镜像大小，同标靶对应镜像大小           | 否       | null     | 见标靶备注                                                   |
| custom_script    | string   | 自定义命令                             | 否       | null     |                                                              |
| init_script      | string   | 初始化命令                             | 否       | null     |                                                              |
| install_script   | string   | 安装命令                               | 否       | null     |                                                              |
| deploy_script    | string   | 部署命令                               | 否       | null     |                                                              |
| clean_script     | string   | 清除命令                               | 否       | null     |                                                              |
| push_flag_script | string   | 推送flag命令                           | 否       | null     |                                                              |
| check_script     | string   | 检查命令                               | 否       | null     |                                                              |
| attack_script    | string   | 攻击命令                               | 否       | null     |                                                              |
| checker          | string   | 检查终端                               | 否       | null     |                                                              |
| attacker         | string   | 攻击终端                               | 否       | null     |                                                              |
| wan_number       | integer  | 虚拟网关wan口数量                      | 否       | 0        |                                                              |
| lan_number       | integer  | 虚拟网关lan口数量                      | 否       | 0        |                                                              |
| external         | integer  | 是否接入外网                           | 否       | false    |                                                              |
| net_configs      | string   | 网络配置                               | 否       | []       |                                                              |
| raw_access_modes | string   | 原始接入方式                           | 否       | []       |                                                              |
| access_modes     | string   | 当前修复的接入方式                     | 否       | []       |                                                              |
| installers       | string   | 安装工具                               | 否       | []       |                                                              |
| tunnel           | string   | 代理隧道                               | 否       | 空       |                                                              |
| status           | integer  | 状态                                   | 否       | 1        |                                                              |
| error            | string   | 错误                                   | 否       | null     |                                                              |
| server_id        | string   | 终端id                                 | 否       | null     |                                                              |
| volumes          | string   | 挂载的卷                               | 否       | []       |                                                              |
| policies         | string   | qos策略                                | 否       | []       |                                                              |
| net_ports        | string   | 网络端口                               | 否       | []       |                                                              |
| float_ip         | string   | 平台可直接访问的ip(直连外网ip或浮动ip) | 否       | null     |                                                              |
| host_ip          | string   | 宿主机ip                               | 否       | null     |                                                              |
| host_name        | string   | 宿主机名称                             | 否       | null     |                                                              |
| host_proxy_port  | string   | 宿主机代理                             | 否       | {}       |                                                              |
| proxy_port       | string   | 平台代理                               | 否       | {}       |                                                              |
| create_time      | datetime | 创建时间                               | 否       | 当前时间 |                                                              |
| created_time     | datetime | 完成时间                               | 否       | null     |                                                              |
| consume_time     | integer  | 消耗时间                               | 否       | 0        |                                                              |
| pause_time       | datetime | 暂停时间                               | 否       | null     |                                                              |
| create_params    | string   | 创建参数                               | 否       | {}       |                                                              |
| float_ip_params  | string   | 浮动ip参数                             | 否       | {}       |                                                              |
| extra            | string   | 其它信息                               | 否       | 空       |                                                              |

## 场景模型设计 CrScene

| 字段 | 类型   | 说明 | 是否必须 | 默认值 | 限制     |
| ---- | ------ | ---- | -------- | ------ | -------- |
| name | string | 名称 | 是       |        | 不可重复 |
| scene_config | 外键 | 指向SceneConfig模型 |是|||
| scene | 外键 | 指向Scene模型 |否|None||
| roles | text | 实例职位允许访问的机器 |是|[]||
| missions | 多对多 | 指向Mission模型 |否|||
| traffic_events | 多对多 | 指向TrafficEvent模型 |否|||
| cr_scene_config | text | 实例配置 |是|{}||
| create_time | datetime | 创建时间 |是|当前时间||
| status | int | 实例状态 |是|1|0-已删除<br />1-正常|

# 实例
## 实例模型设计 CrEvent

| 字段 | 类型   | 说明 | 是否必须 | 默认值 | 限制     |
| ---- | ------ | ---- | -------- | ------ | -------- |
| name | string |  名称  | 是 | | 不可重复 |
| logo | string | 图标 | 是 | event_logo/default_event_logo/img1.png ||
| description | text | 实例描述 | 是 | '' ||
| hash | string |  ||||
| cr_scenes | 外键 | 指向CrScene模型 | 否 |||
| start_time | datetime | 开始时间 | 是 |||
| end_time | datetime | 结束时间 | 是 |||
| status | int | 实例状态 |是| 1| 0-删除 <br />1-正常 <br />2-暂停<br /> 3-进行中 <br />4-已结束|

## 实例和场景多对多自定 CrEventScene 模型

| 字段 | 类型   | 说明 | 是否必须 | 默认值 | 限制     |
| ---- | ------ | ---- | -------- | ------ | -------- |
|  cr_event | 外键 | 指向模型CrEvent |是|||
|  cr_scene | 外键 | 指向模型CrScene |是|||
| name | string  | 关联名称 |是 | '' ||
| roles | text | 职位允许访问用户 | 是| '' ||
| cr_scene_instance | 启动实例场景id | 否 ||||
| extra | text | 额外的信息 |是|''||


## 实例记录用户提交日志模型 CrSceneEventUserSubmitLog

| 字段 | 类型   | 说明 | 是否必须 | 默认值 | 限制     |
| ---- | ------ | ---- | -------- | ------ | -------- |
| user | 外键 | 指向User模型 |否|||
| cr_event | 外键 | 指向CrEvent模型 |是|||
| mission | 外键 | 指向Mission模型 |是|||
| answer | text | 提交答案 |否|||
|score  | float | 获得分数 |是|0||
| is_solved | bool | 是否解决 |是|False||
| is_new | bool | 最新提交 |是|True||
| time | datetime | 提交时间 |是|当前时间||
| submit_ip | string | 提交ip |否|||

## 实例记录用提交答案 CrSceneEventUserAnswer
| 字段 | 类型   | 说明 | 是否必须 | 默认值 | 限制     |
| ---- | ------ | ---- | -------- | ------ | -------- |
|user  | 外键 | 指向User模型 |否|||
| cr_event | 外键 | 指向CrEvent模型 |是|||
| mission | 外键 | 指向Mission模型 |是|||
| answer | text | 提交答案 |否|||
| score | decimal | 分数保留四位小数 |是|0||
| last_edit_time | datetime | 最后编辑时间 |是|当前时间||
| last_edit_user | datetime |  最后编辑者 |否|||

## BaseNotice
| 字段 | 类型   | 说明 | 是否必须 | 默认值 | 限制     |
| ---- | ------ | ---- | -------- | ------ | -------- |
|notice|string|消息|是|||||
|is_topped|bool|是否置顶|是|False|||||
|create_time|datetime|创建时间|是|当前时间||||
|last_edit_time|dateteime|修改时间|是|当前时间|||
|status|int|对象状态|是|1|0-删除 <br /> 1-正常||||


## 实例消息 EventNotice 继承 BaseNotice
| 字段 | 类型   | 说明 | 是否必须 | 默认值 | 限制     |
| ---- | ------ | ---- | -------- | ------ | -------- |
|cr_event| 外键 | 指向CrEvent模型| 是|
|result|text|结果|否|
|machine_id|string|机器id|否|
|create_time|datetime|创建时间|是|


## 任务阶段 MissionPeriod
| 字段 | 类型   | 说明 | 是否必须 | 默认值 | 限制     |
| ---- | ------ | ---- | -------- | ------ | -------- |
|cr_scene|外键|指向模型CrScene|是|
|period_name|string|阶段名称|是|
|period_index|int|第几阶段|是|
|status|int|对象状态|是|1|0-删除<br />1-正常|


## 用户占用标靶信息 CrEventUserStandardDevice
| 字段 | 类型   | 说明 | 是否必须 | 默认值 | 限制     |
| ---- | ------ | ---- | -------- | ------ | -------- |
|ce_event_scene|外键|指向模型CrEventScene|是|
|standard_device|string|标靶id|否|
|scene_id|int|启动的场景id|是|
|status|int|对象状态|是|1|0-删除<br />1-正常|

# 任务

##  检测分类 MonitorCategory

| 字段    | 类型    | 说明     | 是否必须 | 默认值 | 限制                    |
| ------- | ------- | -------- | -------- | ------ | ----------------------- |
| cn_name | string  | 英文名称 | 是       |        | 不可重复，最大长度为100 |
| en_name | string  | 中文名称 | 是       |        | 不可重复，最大长度为100 |
| status  | integer | 记录状态 | 否       | 1      | 0-已删除<br />1-正常    |


## 检测 Scripts

| 字段           | 类型     | 说明            | 是否必须 | 默认值   | 限制                       |
| -------------- | -------- | --------------- | -------- | -------- | -------------------------- |
| type           | integer  | 脚本类型        | 是       | 1        | 0-本地上报<br />1-远程检测 |
| public         | integer  | 是否公开        | 否       | 1        | 似乎没有用到               |
| status         | integer  | 记录状态        | 否       | 1        | 0-已删除<br />1-正常       |
| title          | string   | 标题            | 是       |          | 不可重复,最大长度1024      |
| desc           | string   | 说明            | 否       | null     | 最大长度1024               |
| code           | string   | 脚本中的代码    | 否       |          |                            |
| category       | integer  | 检测类型        | 是       | null     |                            |
| checker        | integer  | 关联的checker机 | 否       | null     |                            |
| suffix         | integer  | 脚本类型        | 是       | 0        | 0-python<br />1-shell      |
| create_time    | datetime | 创建时间        | 否       | 当前时间 |                            |
| create_user    | integer  | 创建用户        | 否       | 当前用户 |                            |
| last_edit_user | integer  | 修改时间        | 否       | 当前时间 |                            |
| last_edit_time | datetime | 修改用户        | 否       | null     |                            |

##  前台实例check日志 CrSceneMissionCheckLog

| 字段       | 类型     | 说明     | 是否必须 | 默认值   | 限制                          |
| ---------- | -------- | -------- | -------- | -------- | ----------------------------- |
| mission    | integer  | 检测任务 | 是       |          |                               |
| user       | integer  | 创建用户 | 否       | null     |                               |
| check_time | datetime | 检测时间 | 否       | 当前时间 |                               |
| cr_event   | integer  | 实例     | 是       | null     |                               |
| score      | float    | 分数     | 否       | 0        |                               |
| is_solved  | boolean  | 是否解决 | 否       | false    | false-未解决<br />true-已解决 |
| target_ip  | string   | check IP | 是       | null     |                               |
| script     | string   | 脚本名称 | 是       | null     |                               |



## 后台测试check日志 CmsTestCheckLog

| 字段       | 类型     | 说明     | 是否必须 | 默认值 | 限制                          |
| ---------- | -------- | -------- | -------- | ------ | ----------------------------- |
| mission    | integer  | 检测任务 | 是       |        |                               |
| user       | integer  | 创建用户 | 否       | null   |                               |
| cr_scene   | integer  | 场景     | 是       | null   |                               |
| check_time | datetime | 检测时间 | 否       | null   |                               |
| score      | float    | 分数     | 否       | 0      |                               |
| is_solved  | boolean  | 是否解决 | 否       | false  | false-未解决<br />true-已解决 |
| target_ip  | string   | check IP | 是       | null   |                               |
| script     | string   | 脚本名称 | 是       | null   |                               |



## 前台实例agent上报检测日志 CrSceneAgentMissionLog

| 字段        | 类型     | 说明     | 是否必须 | 默认值   | 限制                          |
| ----------- | -------- | -------- | -------- | -------- | ----------------------------- |
| mission     | integer  | 检测任务 | 是       |          |                               |
| cr_event    | integer  | 实例     | 是       |          |                               |
| result      | text     | 结果     | 否       | null     |                               |
| is_solved   | boolean  | 是否解决 | 否       | false    | false-未解决<br />true-已解决 |
| create_time | datetime | 创建时间 | 否       | 当前时间 |                               |



## 后台测试agent上报检测日志 CmsAgentTestCheckLog

| 字段        | 类型     | 说明     | 是否必须 | 默认值   | 限制                          |
| ----------- | -------- | -------- | -------- | -------- | ----------------------------- |
| mission     | integer  | 检测任务 | 是       |          |                               |
| cr_scene    | integer  | 实例     | 是       |          |                               |
| result      | text     | 结果     | 否       | null     |                               |
| is_solved   | boolean  | 是否解决 | 否       | false    | false-未解决<br />true-已解决 |
| create_time | datetime | 创建时间 | 否       | 当前时间 |                               |



## 后台测试结果 CmsTestCheckRecord

| 字段        | 类型     | 说明     | 是否必须 | 默认值   | 限制 |
| ----------- | -------- | -------- | -------- | -------- | ---- |
| mission     | integer  | 检测任务 | 是       |          |      |
| user        | integer  | 创建用户 | 否       | null     |      |
| cr_scene    | integer  | 场景     | 是       | null     |      |
| submit_time | datetime | 检测时间 | 否       | 当前时间 |      |
| score       | float    | 分数     | 否       | 0        |      |
| target_ip   | string   | check IP | 是       | null     |      |
| script      | string   | 脚本名称 | 是       | null     |      |


# 评估模块

## 检测报告 CkeckReport

| 字段        | 类型     | 说明       | 是否必须 | 默认值   | 限制 |
| ----------- | -------- | ---------- | -------- | -------- | ---- |
| cr_event    | integer  | 对应场景id | 是       |          |      |
| result      | string   | 检测结果   | 是       |          |      |
| machine_id  | integer  | 机器id     | 是       |          |      |
| create_time | datetime | 创建时间   | 是       | 当前时间 |      |

## 评估报告 EvaluationReport

| 字段              | 类型    | 说明           | 是否必须 | 默认值 | 限制                                 |
| ----------------- | ------- | -------------- | -------- | ------ | ------------------------------------ |
| report            | integer | 对应检测报告id | 是       |        |                                      |
| evaluation_status | integer | 评估结果       | 是       | 0      | 0-待评估<br />1-已确认<br />2-已驳回 |
| evaluator         | integer | 评估人         | 否       |        |                                      |
| status            | integer | 评估状态       | 是       | 1      | 0-已删除<br />1-正常                 |

# 任务模块模型设计

## 公共字段 Mission

| 字段           | 类型     | 说明         | 是否必须 | 默认值   | 限制                                                         |
| -------------- | -------- | ------------ | -------- | -------- | ------------------------------------------------------------ |
| title          | string   | 名称         | 是       |          |                                                              |
| type           | integer  | 类型         | 是       |          | 0-试卷型<br />1-CTF型<br />2-检测型                          |
| content        | string   | 具体内容     | 否       |          |                                                              |
| score          | integer  | 总分         | 是       |          |                                                              |
| status         | integer  | 状态         | 是       | 1        | 0-已删除<br />1-正常                                         |
| period         | integer  | 阶段         | 是       |          |                                                              |
| public         | boolean  | 是否公开     | 是       | False    |                                                              |
| difficulty     | integer  | 难度         | 是       | 0        | 0-简单<br />1-一般<br />2-困难                               |
| mission_status | integer  | 进行状态     | 是       | 0        | 0-未开始<br />1-进行中<br />2-暂停<br />3-客户端错误<br />4-运行错误 |
| create_time    | datetime | 创建时间     | 否       | 当前时间 |                                                              |
| create_user    | integer  | 创建用户     | 否       | 当前用户 |                                                              |
| lase_edit_time | datetime | 最后编辑时间 | 否       | 当前时间 |                                                              |
| last_edit_user | integer  | 最后编辑用户 | 否       | 当前用户 |                                                              |

## 私有字段 与Mission一对一关联

## 试卷型 ExamTask

| 字段         | 类型    | 说明       | 是否必须 | 默认值 | 限制                                       |
| ------------ | ------- | ---------- | -------- | ------ | ------------------------------------------ |
| exam         | integer | 对应任务id | 是       |        |                                            |
| task_title   | string  | 标题       | 是       |        |                                            |
| task_content | string  | 具体内容   | 是       |        |                                            |
| task_type    | integer | 题型       | 是       |        | 0-单选<br />1-多选<br />2-判断<br />3-简答 |
| option       | string  | 选项       | 否       |        |                                            |
| answer       | string  | 答案       | 是       |        |                                            |
| task_index   | integer | 序号       | 是       |        |                                            |
| task_score   | integer | 分数       | 是       |        |                                            |
| status       | integer | 状态       | 是       |        | 0-已删除<br />1-正常                       |

## CTF型 CTFMission

| 字段    | 类型    | 说明       | 是否必须 | 默认值 | 限制 |
| ------- | ------- | ---------- | -------- | ------ | ---- |
| mission | integer | 对应任务id | 是       |        |      |
| target  | string  | 靶机       | 是       |        |      |
| flag    | string  | flag       | 是       |        |      |

## 检测型 CheckMission

| 字段               | 类型    | 说明           | 是否必须 | 默认值 | 限制                        |
| ------------------ | ------- | -------------- | -------- | ------ | --------------------------- |
| mission            | integer | 对应任务id     | 是       |        |                             |
| check_type         | integer | 检测类型       | 是       |        | 0-系统检测<br />1-agent上报 |
| checker_id         | string  | 检测机         | 否       | 空     | 系统检测任务必须有该字段    |
| target_net         | string  | 靶机所在网络   | 否       | 空     | 系统检测任务必须有该字段    |
| target             | string  | 靶机           | 是       |        |                             |
| scripts            | string  | 脚本名         | 是       |        |                             |
| is_once            | boolean | 是否只检测一次 | 是       | False  |                             |
| first_check_time   | integer | 首次检测时间   | 否       | 0      |                             |
| is_polling         | boolean | 是否轮询       | 否       | False  |                             |
| interval           | integer | 检测时间间隔   | 否       |        | 检测多次的情况下必须有      |
| params             | string  | 检测脚本参数   | 否       | 空     |                             |
| status_description | string  | 状态描述       | 否       | 空     |                             |

# 流量模型设计

## 流量分类 TrafficCategory

| 字段                         | 类型                         | 说明                           | 是否必须 | 默认值   | 限制 |
| ------------------------------ | -------- | -------- | -------- | -------- | -------- |
| cn_name                | string                 | 中文名称                       | 是       |          | 长度2~20个字符，唯一 |
| en_name                | string                 | 英文名称                   | 是       |          | 长度2~20个字符，唯一 |
|  status                        |  string                        |  状态                              | 是       | 1 | 0-删除<br />1-正常 |


## 流量 Traffic

| 字段                         | 类型                         | 说明                           | 是否必须 | 默认值   | 限制 |
| ------------------------------ | -------- | -------- | -------- | -------- | -------- |
| title           | string                 | 名称                       | 是    |          | 长度2~20个字符，唯一 |
| introduction    | string                 | 简介                     | 是     | ‘ ’ | 长度2~1000个字符 |
|  type                    |  integer                 |  类型                            | 否      | 1 | 1-背景流量<br />2-智能流量 |
| public | boolean | 是否公开 | 是 | True | |
| is_copy | boolean | 是否拷贝 | 否 | False | |
| hash | string | hash | 否 |  | |
| category | foreignKey | 指向TrafficCategory | 是 |  | |
| create_time | datetime | 创建日期 | 否 | 当前时间 | |
| create_user | foreignKey | 创建用户 | 是 | 当前用户 | |
| last_edit_user | foreignKey | 最后编辑用户 | 是 | 修改用户 | |
| last_edit_time | datetime | 最后编辑日期 | 否 | 修改时间 | |
| status | integer | 状态 | 否 | 1 | 0-删除<br />1-正常         |
| parent | integer | 由谁拷贝 | 否 |  | |



## 背景流量 BackgroundTraffic

| 字段                         | 类型                         | 说明                           | 是否必须 | 默认值   | 限制 |
| ------------------------------ | -------- | -------- | -------- | -------- | -------- |
| traffic         | OneToOne | 指向Traffic模型            | 是       |          | 主键 |
| pcap_file       | file                 | pcap文件               | 否     |          |          |
|  file_name               |  string                        |  文件名                          | 否     |  | 长度2~20个字符，必须 |
| trm | foreignKey | 指向StandardDevice模型 | 是 | null | |
| loop | integer | 重放次数 | 否 | 1 | 0-循环<br />1-一次<br />最小值0，最大值10 |
| mbps | integer | 频率 | 否 |  | 最小值0，最大值10 |
| multiplier | integer | 倍速 | 否 |  | 最小值0，最大值10 |



##  智能流量 IntelligentTraffic

| 字段                         | 类型                         | 说明                           | 是否必须 | 默认值   | 限制 |
| ------------------------------ | -------- | -------- | -------- | -------- | -------- |
| traffic         | OneToOne | 指向Traffic模型          | 是       |          | 主键 |
| code            | string                 | 脚本内容       | 否      | null |          |
|  file_name               |  string                        |  状态                              | 否      |  |  |
| suffix | integer | 后缀(脚本类型) | 否 |  | 0-python<br />1-shell |
| tgm | foreignKey | 指向StandardDevice模型 | 是 | null | |



## 流量事件 TrafficEvent

| 字段                         | 类型                         | 说明                           | 是否必须 | 默认值   | 限制 |
| ------------------------------ | -------- | -------- | -------- | -------- | -------- |
| title           | string                 | 名称                       | 是    |          | 长度2~20个字符，唯一 |
| introduction    | string                 | 简介         | 是     | ' ' | 长度2~1000个字符 |
|  type                    |  integer                 |  类型                            | 否      | 1 | 1-背景事件<br />2-智能事件 |
| start_up_mode | integer | 启动模式 | 是 | 1 | 1-自动启动<br />2-延迟启动 |
| delay_time | integer | 延迟时间 | 否 |  | |
| public | boolean | 是否公开 | 否 | True | |
| traffic | foreignKey | 流量 | 是 |  | |
| target | string | 目标机器 | 否 | null | 最大长度128 |
| runner | string | 发生机器 | 否 | null | 最大长度100 |
| target_net | string | 目标网络 | 否 | null | 最大长度100 |
| parameter | string | 其他参数 | 否 | null | 最大长度200 |
| pid | string | 进程ID | 否 | null | 最大长度128 |
| create_time | datetime | 创建日期 | 否 | 当前时间 | |
| create_user | foreignKey | 创建者 | 是 | 当前用户 | |
| last_edit_user | foreignKey | 最后编辑者 | 是 | 修改用户 | |
| last_edit_time | datetime | 最后编辑日期 | 否 | 修改时间 | |
| status | integer | 状态 | 否 | 1 | 0-删除<br />1-正常<br />2-运行中<br />3-错误 |
| error | string | 错误信息 | 否 | null | 最大长度2048 |

