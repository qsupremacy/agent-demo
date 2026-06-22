# green-skill 家电状态获取技能

## 概述

green-skill 是 OfficeClaw 平台的家电状态获取技能，从远程服务器实时拉取家庭家电运行数据，支持空调、冰箱、灯具、电视四类设备的状态查询。

## 数据来源

- 远程地址：`http://101.34.223.37/appliance-status.json`
- 防缓存策略：每次请求自动追加时间戳参数 `?t=<毫秒级时间戳>`

## 支持设备

| 设备 | 字段 | 状态信息 |
|------|------|----------|
| 空调 | `air_conditioner` | 模式、设定温度、室温、风速、运行时长 |
| 冰箱 | `refrigerator` | 冷藏温度、冷冻温度、运行模式、门状态、耗电量 |
| 灯具 | `lights` | 客厅、卧室、厨房、走廊灯状态、色温 |
| 电视 | `tv` | 电源状态、频道、音量、使用时长、信号源 |

## 文件结构

```
navagent/skills/
├── __init__.py          # 模块导出
├── green_skill.py       # 技能实现
└── README.md            # 本文件
```

## 接口说明

### fetch_appliance_status()

异步获取原始家电状态数据。

```python
from skills.green_skill import fetch_appliance_status

result = await fetch_appliance_status()

# 成功
# {"status": "success", "data": { "air_conditioner": {...}, ... }}

# 失败
# {"status": "error", "error": "请求超时，远程服务无响应"}
```

### format_status_text(data)

将原始数据格式化为可读文本。

```python
from skills.green_skill import format_status_text

text = format_status_text(result["data"])
# 输出示例：
# 【空调】运行中
#   - 制冷
#   - 26°C
#   ...
```

### GreenSkillTool

LangChain 工具封装，可直接注册为 Agent 工具。

```python
from skills.green_skill import GreenSkillTool

tool = GreenSkillTool()

# 异步调用
result = await tool.arun("查看家电状态")

# 同步调用
result = tool.run("查看家电状态")
```

工具属性：

| 属性 | 值 |
|------|-----|
| `name` | `get_appliance_status` |
| `description` | 获取家庭家电实时状态，包括空调、冰箱、灯具、电视的运行信息 |

## 在 Agent 中集成

```python
from skills import GreenSkillTool

tool = GreenSkillTool()
agent = create_agent(model=llm, tools=[tool], system_prompt=system_prompt)
```

## 错误处理

| 错误类型 | 返回信息 |
|----------|----------|
| 请求超时 | `请求超时，远程服务无响应` |
| HTTP 错误 | `HTTP 错误: <状态码>` |
| 格式异常 | `远程返回数据格式异常` |
| 其他异常 | `获取失败: <异常详情>` |

## 依赖

- `httpx` — 异步 HTTP 客户端
