---
name: green-skill
description: 获取和控制家庭家电。当用户询问家电状态、开关设备（空调/冰箱/灯具/电视）时使用此技能。支持查询实时状态和独立开关设备。
---

# green-skill 家电状态与控制技能

## 功能说明

从远程服务器获取家庭家电的实时运行状态，并支持独立开关设备。

支持设备：

- 空调：模式、温度、风速、运行时长
- 冰箱：冷藏/冷冻温度、运行模式、门状态、耗电量
- 灯具：各房间灯具开关与亮度、色温
- 电视：电源状态、频道、音量、使用时长、信号源

## 数据来源

- 状态查询：`GET http://101.34.223.37/api/status`
- 设备控制：`PATCH http://101.34.223.37/api/status/{device}/{field}`

## 使用方式

### 查询状态

```python
import asyncio
from scripts.main import fetch_appliance_status, format_status_text

result = await fetch_appliance_status()
if result["status"] == "success":
    print(format_status_text(result["data"]))
```

### 开关设备

```python
from scripts.main import toggle_device

# 打开空调（支持中文名或英文 key）
result = await toggle_device("空调", "on")

# 关闭电视
result = await toggle_device("tv", "off")
```

### 作为 LangChain 工具注册

```python
from scripts.main import GreenSkillTool, ToggleDeviceTool

tools = [GreenSkillTool(), ToggleDeviceTool()]
agent = create_agent(model=llm, tools=tools, system_prompt=system_prompt)
```

| 工具 | 名称 | 说明 |
|------|------|------|
| `GreenSkillTool` | `get_appliance_status` | 查询全部家电状态 |
| `ToggleDeviceTool` | `toggle_appliance` | 开关设备，输入格式: `<设备名> <on\|off>` |
