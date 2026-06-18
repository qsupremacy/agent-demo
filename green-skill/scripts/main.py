"""
green-skill - 家电状态获取与控制技能

从远程地址获取家庭家电实时状态数据，支持空调、冰箱、灯具、电视等设备。
支持查询状态和独立开关设备。
数据来源：http://101.34.223.37/api/status
"""

import json
from typing import Dict, Any, Optional

import httpx

REMOTE_URL = "http://101.34.223.37/api/status"

# 设备中文名映射
DEVICE_NAMES = {
    "air_conditioner": "空调",
    "refrigerator": "冰箱",
    "lights": "灯具",
    "tv": "电视",
}

# 中文名 → 设备 key 反向映射
NAME_TO_KEY = {v: k for k, v in DEVICE_NAMES.items()}

# 设备开启时的默认状态文本
DEVICE_ON_TEXT = {
    "air_conditioner": "运行中",
    "refrigerator": "运行中",
    "lights": "已开启",
    "tv": "播放中",
}

STATUS_TEXT = {"on": "运行中", "off": "已关闭"}


def _resolve_device(device: str) -> Optional[str]:
    """
    解析设备标识，支持英文 key 和中文名。

    Args:
        device: 设备标识，如 "air_conditioner" 或 "空调"

    Returns:
        设备 key，无效时返回 None
    """
    if device in DEVICE_NAMES:
        return device
    return NAME_TO_KEY.get(device)


async def fetch_appliance_status() -> Dict[str, Any]:
    """
    从远程地址获取全部家电状态。

    Returns:
        {"status": "success", "data": {...}} 或 {"status": "error", "error": "..."}
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(REMOTE_URL)
            resp.raise_for_status()
            data = resp.json()
        return {"status": "success", "data": data}
    except httpx.TimeoutException:
        return {"status": "error", "error": "请求超时，远程服务无响应"}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "error": f"HTTP 错误: {e.response.status_code}"}
    except json.JSONDecodeError:
        return {"status": "error", "error": "远程返回数据格式异常"}
    except Exception as e:
        return {"status": "error", "error": f"获取失败: {str(e)}"}


async def toggle_device(device: str, action: str) -> Dict[str, Any]:
    """
    开关指定设备。

    Args:
        device: 设备标识（英文 key 或中文名），如 "air_conditioner" 或 "空调"
        action: "on" 打开 或 "off" 关闭

    Returns:
        {"status": "success", "device": "...", "action": "...", "message": "..."}
        或 {"status": "error", "error": "..."}
    """
    device_key = _resolve_device(device)
    if not device_key:
        valid = "、".join(f"{k}({v})" for k, v in DEVICE_NAMES.items())
        return {"status": "error", "error": f"无效设备: {device}，可选: {valid}"}

    if action not in ("on", "off"):
        return {"status": "error", "error": f"无效操作: {action}，可选: on、off"}

    device_name = DEVICE_NAMES[device_key]
    status_text = DEVICE_ON_TEXT[device_key] if action == "on" else "已关闭"

    url = f"{REMOTE_URL}/{device_key}/status"
    url_text = f"{REMOTE_URL}/{device_key}/status_text"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # 更新 status 字段
            resp1 = await client.patch(url, json={"value": action})
            resp1.raise_for_status()
            # 更新 status_text 字段
            resp2 = await client.patch(url_text, json={"value": status_text})
            resp2.raise_for_status()

        action_text = "已打开" if action == "on" else "已关闭"
        return {
            "status": "success",
            "device": device_key,
            "device_name": device_name,
            "action": action,
            "message": f"{device_name}{action_text}",
        }

    except httpx.TimeoutException:
        return {"status": "error", "error": "请求超时，远程服务无响应"}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "error": f"HTTP 错误: {e.response.status_code}"}
    except Exception as e:
        return {"status": "error", "error": f"操作失败: {str(e)}"}


def format_status_text(data: Dict[str, Any]) -> str:
    """将家电状态数据格式化为可读文本。"""
    if not data:
        return "暂无数据"

    lines = []
    for key, name in DEVICE_NAMES.items():
        device = data.get(key)
        if not device:
            continue

        status = STATUS_TEXT.get(device.get("status", ""), device.get("status_text", "未知"))
        lines.append(f"【{name}】{status}")

        for field_key, field_value in device.items():
            if field_key in ("status", "status_text"):
                continue
            lines.append(f"  - {field_value}")

    return "\n".join(lines) if lines else "暂无数据"


# --- LangChain 工具封装 ---

class GreenSkillTool:
    """
    查询家电状态工具。

    Attributes:
        name: 工具名称
        description: 工具描述
    """

    name = "get_appliance_status"
    description = "获取家庭家电实时状态，包括空调、冰箱、灯具、电视的运行信息"

    async def arun(self, query: str = "") -> str:
        result = await fetch_appliance_status()
        if result["status"] == "error":
            return f"获取家电状态失败: {result['error']}"
        return format_status_text(result["data"])

    def run(self, query: str = "") -> str:
        import asyncio
        return asyncio.run(self.arun(query))


class ToggleDeviceTool:
    """
    开关家电工具。

    Attributes:
        name: 工具名称
        description: 工具描述
    """

    name = "toggle_appliance"
    description = (
        "开关家庭家电设备。参数格式: <设备名> <on|off>，"
        "支持的设备: air_conditioner(空调)、refrigerator(冰箱)、lights(灯具)、tv(电视)。"
        "示例: '空调 on'、'tv off'"
    )

    async def arun(self, query: str = "") -> str:
        """
        解析输入并执行开关操作。

        Args:
            query: 格式为 "<设备名> <on|off>"，如 "空调 on"
        """
        parts = query.strip().split()
        if len(parts) != 2:
            return "参数格式错误，请使用: <设备名> <on|off>，例如: 空调 on"

        device, action = parts
        result = await toggle_device(device, action)

        if result["status"] == "error":
            return f"操作失败: {result['error']}"
        return result["message"]

    def run(self, query: str = "") -> str:
        import asyncio
        return asyncio.run(self.arun(query))
