#**thrift返回结果格式：**
```
    {
        "status": {status},
        "content": {script check result}
    }
```
**{status}定义:**
```
    {
        "up": "client连上service",
        "down": "client连不上service",
        "error": "命令、脚本在service上运行错误"
    }
```
##**script check result 定义**:
+ script check result为脚本执行后返回的值

+ **1.python脚本thrift返回值:**
```
        {
            "status": {status},
            "content": {
                "check": {check_status},
                "msg": {msg}
            }
        }

        {check_status}:
            "success": 表示check成功,
            "fail": 表示check失败

        {msg}:
            "xxxxx": 返回信息(自定义)
```
+ 1-1.python检测脚本格式:
```
            #必须含有名为checker的函数，返回值为{"check": {check_status}, "msg": {msg}}:
            #例如：
                def checker(ip, port):
                    ...
                    ret = {
                        "check": "success",
                        "msg": "check success"
                    }
                    return ret
```

+ **2.shell脚本thrift返回值:**
```
        {
            "status": {status},
            "content": {script result}
        }
        {script result}:
            "CheckUp": "检测成功"
            "CheckDown": "检测失败"
```

+ 2-1.shell检测脚本：
```
    #必须含有返回值:
        "CheckUp": "检测成功",
        "CheckDown": "检测失败"
    #例如：
        ping $1 -c 2 -w 1 | grep -q "ttl=" && echo "CheckUp" || echo "CheckDown"
```



## agent上报

#### 启动参数
```
    {
        "scene_hash" : { scene_hash }      #场景hash
        "machine_id" : { machine_id }      #机器id
        "interval" : { interval }          #检查时间间隔
    }
````

#### 返回参数

```
    {
        'CPU': {'usage': '8.1%'},
        'memory': {'usage': '59.9%', 'total': '11GB', 'used': '5GB'},
        'disk': {'usage': '46.5%', 'total': '97GB', 'used': '43GB'}
    }
```





## 日志优化
