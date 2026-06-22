"""
家电状态远程修改 API（多用户版）

提供读取和修改 appliance-status.json 的 RESTful 接口。
支持多用户，每个用户拥有独立的家电设备数据。
"""

import json
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from filelock import FileLock
from pydantic import BaseModel

app = FastAPI(title="家电状态 API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

JSON_PATH = os.environ.get("APPLIANCE_JSON_PATH", "/usr/share/nginx/html/appliance-status.json")
LOCK_PATH = JSON_PATH + ".lock"

VALID_DEVICES = {"air_conditioner", "refrigerator", "lights", "tv"}


def _read_json() -> Dict[str, Any]:
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="状态文件不存在")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="状态文件格式异常")


def _write_json(data: Dict[str, Any]):
    lock = FileLock(LOCK_PATH)
    with lock:
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


def _validate_device(device: str):
    if device not in VALID_DEVICES:
        raise HTTPException(status_code=400, detail=f"无效设备: {device}，可选: {', '.join(VALID_DEVICES)}")


def _validate_user(data: Dict, user: str):
    if user not in data:
        raise HTTPException(status_code=404, detail=f"用户 {user} 不存在，现有用户: {', '.join(data.keys())}")


class FieldUpdate(BaseModel):
    value: Any


class DeviceRegister(BaseModel):
    data: Dict[str, Any] = {"status": "off"}


# --- 接口 ---

@app.get("/api/status", summary="获取所有用户的家电状态")
def get_all_status():
    """返回所有用户及其设备的完整数据。"""
    return _read_json()


@app.get("/api/status/{user}", summary="获取指定用户的家电状态")
def get_user_status(user: str):
    """返回指定用户的全部设备状态。"""
    data = _read_json()
    _validate_user(data, user)
    return data[user]


@app.get("/api/status/{user}/{device}", summary="获取指定用户的指定设备状态")
def get_device_status(user: str, device: str):
    data = _read_json()
    _validate_user(data, user)
    if device not in data[user]:
        raise HTTPException(status_code=404, detail=f"用户 {user} 无设备 {device}")
    return data[user][device]


@app.post("/api/device/{user}/{device}", summary="注册设备")
def register_device(user: str, device: str, payload: DeviceRegister):
    """为指定用户注册一个新设备，提供初始状态数据。"""
    data = _read_json()
    _validate_user(data, user)
    if device in data[user]:
        raise HTTPException(status_code=409, detail=f"用户 {user} 已有设备 {device}，如需更新请使用 PUT")
    data[user][device] = payload.data
    _write_json(data)
    return {"message": f"设备 {device} 已注册到用户 {user}", "device": device, "data": payload.data}


@app.delete("/api/device/{user}/{device}", summary="注销设备")
def unregister_device(user: str, device: str):
    """从指定用户中注销（删除）一个设备。"""
    data = _read_json()
    _validate_user(data, user)
    if device not in data[user]:
        raise HTTPException(status_code=404, detail=f"用户 {user} 无设备 {device}")
    removed = data[user].pop(device)
    _write_json(data)
    return {"message": f"设备 {device} 已从用户 {user} 中注销", "device": device, "removed_data": removed}


@app.put("/api/status/{user}/{device}", summary="更新指定用户的指定设备全部状态")
def update_device(user: str, device: str, payload: Dict[str, Any]):
    data = _read_json()
    _validate_user(data, user)
    data[user][device] = payload
    _write_json(data)
    return {"message": f"用户 {user} 的设备 {device} 已更新", "data": payload}


@app.patch("/api/status/{user}/{device}/{field}", summary="更新指定用户设备的单个字段")
def update_field(user: str, device: str, field: str, payload: FieldUpdate):
    data = _read_json()
    _validate_user(data, user)
    if device not in data[user]:
        raise HTTPException(status_code=404, detail=f"用户 {user} 无设备 {device}")
    data[user][device][field] = payload.value
    _write_json(data)
    return {"message": f"{user}.{device}.{field} 已更新为 {payload.value}", "field": field, "value": payload.value}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
