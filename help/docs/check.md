**任务类型**

   - 试卷型
      - 题目类型
      - 步骤
   - CTF型
      - 步骤
   - 检测型
      - 检测型类型
      - 步骤
      - 说明
      - 参数注意事项
      - 注意事项
   - 任务执行次数以及计分规则



----------

# 检测类型

- 远程检测
- 本地检测

------

## 远程检测

### 新建远程检测步骤

1. 在CGM管理中，新建checker机器，并设置所需环境（若已有所需的checker机器，可跳过此步）

2. 新建远程检测，**并关联checker机**

   ![](./img/远程检测.png)

   **说明：**

      - 脚本格式请参照 - [脚本来源说明](#script_format)
      - 脚本来源支持多种方式，请参考-[脚本来源说明](#script_source)
      - 若无“类型”，请返回列表页面，新建类型，
      - 若无“Checker”， 请在CGM管理中，新建checker机器，详情参考第一步
      - 脚本支持python和shell语言

------

## 本地检测

### 新建本地检测步骤

1. 新建本机检测， **无需关联checker机**

   ![](./img/本地检测.png)

   **说明：**

      - 脚本格式请参照 - [脚本来源说明](#script_format)
      - 脚本来源支持多种方式，请参考-[脚本来源说明](#script_source)
      - 若无“类型”，请返回列表页面，新建类型，
      - 脚本支持python和shell语言

------

## <span id="script_source">脚本来源说明</span>

1. 在线编写
2. 上传脚本
3. 从已有脚本中选择/修改，***不影响已有脚本***

------

## 脚本格式

### 1. python检测脚本格式

   必须含有名为**checker**的函数,
   返回值为：**{"check": {check_status}, "msg": {msg}}**
   返回值说明：

  ```
{
    "check": {check_status},
    "msg": {msg}
}        
  
{check_status}:
	"success": 表示check成功,
	"fail": 表示check失败

{msg}:
	"xxxxx": 返回信息(自定义)

  ```
   例如：

   ```python
def checker(ip, port=80, **kwargs):
    import socket
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.settimeout(1)
    try:
        sk.connect((ip, port))
        ret = {
            "check": "success",
            "msg": "Check Success"
        }
    except Exception as e:
        ret = {
            "check": "fail",
            "msg": str(e)
        }
    return ret
   ```

### 2. shell检测脚本格式
   必须含有返回值:

```
"CheckUp": "检测成功",
"CheckDown": "检测失败"
```

   例如：

```
ping $1 -c 2 -w 1 | grep -q "ttl=" && echo "CheckUp" || echo "CheckDown"
```

