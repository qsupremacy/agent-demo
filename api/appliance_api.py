"""
家电状态远程修改 API

提供读取和修改 appliance-status.json 的 RESTful 接口。
部署于远程服务器，通过 nginx 反向代理对外提供服务。
"""

import json
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from filelock import FileLock
from pydantic import BaseModel

app = FastAPI(title="家电状态 API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# JSON 文件路径，可通过环境变量覆盖
JSON_PATH = os.environ.get("APPLIANCE_JSON_PATH", "/usr/share/nginx/html/appliance-status.json")
LOCK_PATH = JSON_PATH + ".lock"

VALID_DEVICES = {"air_conditioner", "refrigerator", "lights", "tv"}


def _read_json() -> Dict[str, Any]:
    """读取 JSON 文件。"""
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="状态文件不存在")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="状态文件格式异常")


def _write_json(data: Dict[str, Any]):
    """写入 JSON 文件（带文件锁）。"""
    lock = FileLock(LOCK_PATH)
    with lock:
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


# --- 请求模型 ---

class FieldUpdate(BaseModel):
    value: Any


# --- 接口 ---

@app.get("/api/status", summary="获取全部家电状态")
def get_status():
    """返回所有设备的当前状态。"""
    return _read_json()


@app.get("/api/status/{device}", summary="获取指定设备状态")
def get_device_status(device: str):
    """返回指定设备的当前状态。"""
    if device not in VALID_DEVICES:
        raise HTTPException(status_code=400, detail=f"无效设备: {device}，可选: {', '.join(VALID_DEVICES)}")
    data = _read_json()
    if device not in data:
        raise HTTPException(status_code=404, detail=f"设备 {device} 数据不存在")
    return data[device]


@app.put("/api/status/{device}", summary="更新指定设备全部状态")
def update_device(device: str, payload: Dict[str, Any]):
    """用传入的数据完整替换指定设备的状态。"""
    if device not in VALID_DEVICES:
        raise HTTPException(status_code=400, detail=f"无效设备: {device}，可选: {', '.join(VALID_DEVICES)}")
    data = _read_json()
    data[device] = payload
    _write_json(data)
    return {"message": f"设备 {device} 状态已更新", "data": payload}


@app.patch("/api/status/{device}/{field}", summary="更新指定设备的单个字段")
def update_field(device: str, field: str, payload: FieldUpdate):
    """仅修改指定设备的某个字段值。"""
    if device not in VALID_DEVICES:
        raise HTTPException(status_code=400, detail=f"无效设备: {device}，可选: {', '.join(VALID_DEVICES)}")
    data = _read_json()
    if device not in data:
        raise HTTPException(status_code=404, detail=f"设备 {device} 数据不存在")
    data[device][field] = payload.value
    _write_json(data)
    return {"message": f"{device}.{field} 已更新为 {payload.value}", "field": field, "value": payload.value}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
