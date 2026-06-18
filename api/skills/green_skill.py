"""
green-skill - 家电状态获取技能

从远程地址获取家庭家电实时状态数据，支持空调、冰箱、灯具、电视等设备。
数据来源：http://101.34.223.37/appliance-status.json
"""

import time
import json
from typing import Dict, Any, Optional

import httpx

REMOTE_URL = "http://101.34.223.37/appliance-status.json"

# 设备中文名映射
DEVICE_NAMES = {
    "air_conditioner": "空调",
    "refrigerator": "冰箱",
    "lights": "灯具",
    "tv": "电视",
}

STATUS_TEXT = {"on": "运行中", "off": "已关闭"}


async def fetch_appliance_status() -> Dict[str, Any]:
    """
    从远程地址获取家电状态。

    每次请求在 URL 后追加时间戳参数以避免缓存。

    Returns:
        包含各家电状态数据的字典，格式：
        {
            "status": "success" | "error",
            "data": { ... },       # 成功时
            "error": "..."         # 失败时
        }
    """
    url = f"{REMOTE_URL}?t={int(time.time() * 1000)}"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
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


class GreenSkillTool:
    """
    LangChain 工具封装，可直接注册为 Agent 工具使用。

    Usage:
        tool = GreenSkillTool()
        result = await tool.arun("查看家电状态")
    """

    name = "get_appliance_status"
    description = "获取家庭家电实时状态，包括空调、冰箱、灯具、电视的运行信息"

    async def arun(self, query: str = "") -> str:
        """异步执行，返回格式化的状态文本。"""
        result = await fetch_appliance_status()

        if result["status"] == "error":
            return f"获取家电状态失败: {result['error']}"

        return format_status_text(result["data"])

    def run(self, query: str = "") -> str:
        """同步执行（内部使用 asyncio）。"""
        import asyncio
        return asyncio.run(self.arun(query))
