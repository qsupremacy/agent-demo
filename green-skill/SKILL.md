---
name: green-skill
description: 通过 curl 命令查询和控制家庭家电设备状态。基于 OfficeClaw 智能体平台的多用户家电管理，支持查询状态、开关设备、注册和注销设备。使用前请先阅读本文件中的 curl 示例。
---

# green-skill 家电状态与控制技能

## 概述

本技能通过 curl 命令与远程 API 通信，实现多用户、多设备的家电管理。

- **基础地址**：`http://101.34.223.37`
- **数据格式**：JSON
- **认证方式**：无（内部网络）

## 通用参数说明

| 参数 | 说明 |
|------|------|
| `{user}` | 用户名（必填），如 `haolipeng`、`dinglaiqiang` |
| `{device}` | 设备 key，如 `air_conditioner`、`refrigerator`、`lights`、`tv` |
| `{field}` | 设备内的字段名，如 `status`、`mode`、`target_temp` |

**重要**：所有用户操作必须明确指定 `{user}`，不允许使用默认值。

## 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/status` | 获取所有用户 |
| `GET` | `/api/status/{user}` | 获取指定用户全部设备 |
| `GET` | `/api/status/{user}/{device}` | 获取指定用户的指定设备 |
| `POST` | `/api/device/{user}/{device}` | 注册设备 |
| `DELETE` | `/api/device/{user}/{device}` | 注销设备 |
| `PATCH` | `/api/status/{user}/{device}/{field}` | 修改设备字段 |
| `PUT` | `/api/status/{user}/{device}` | 替换设备全部状态 |

## curl 命令示例

### 1. 查询所有用户状态

```bash
curl -s http://101.34.223.37/api/status
```

### 2. 查询指定用户状态

```bash
# 英文用户名
curl -s http://101.34.223.37/api/status/haolipeng

# 中文用户名（如有）
curl -s "http://101.34.223.37/api/status/张三"
```

### 3. 查询指定设备状态

```bash
curl -s http://101.34.223.37/api/status/haolipeng/air_conditioner
```

### 4. 开关设备（修改 status 字段）

```bash
# 打开空调
curl -s -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"value":"on"}' \
  http://101.34.223.37/api/status/haolipeng/air_conditioner/status

# 关闭电视
curl -s -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"value":"off"}' \
  http://101.34.223.37/api/status/dinglaiqiang/tv/status
```

### 5. 修改设备的非状态字段

```bash
# 修改空调设定温度为 24°C
curl -s -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"value":"24°C"}' \
  http://101.34.223.37/api/status/haolipeng/air_conditioner/target_temp

# 修改电视音量
curl -s -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"value":"25"}' \
  http://101.34.223.37/api/status/haolipeng/tv/volume
```

### 6. 替换设备全部状态

```bash
curl -s -X PUT \
  -H "Content-Type: application/json" \
  -d '{"status":"on","mode":"制冷","target_temp":"26°C","room_temp":"27°C","fan_speed":"自动","runtime":"1小时"}' \
  http://101.34.223.37/api/status/haolipeng/air_conditioner
```

### 7. 注册新设备

```bash
# 注册洗衣机
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"data":{"status":"off","mode":"标准洗","water_temp":"30°C","remaining":"--"}}' \
  http://101.34.223.37/api/device/haolipeng/washing_machine

# 使用最小数据注册（默认 status=off）
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"data":{"status":"off"}}' \
  http://101.34.223.37/api/device/haolipeng/robot_vacuum
```

### 8. 注销设备

```bash
# 注销洗衣机
curl -s -X DELETE \
  http://101.34.223.37/api/device/haolipeng/washing_machine
```

## 预定义设备

| key | 中文名 | 常用字段 |
|-----|--------|----------|
| `air_conditioner` | 空调 | `status`, `mode`, `target_temp`, `room_temp`, `fan_speed`, `runtime` |
| `refrigerator` | 冰箱 | `status`, `fridge_temp`, `freezer_temp`, `mode`, `door`, `power_today` |
| `lights` | 灯具 | `status`, `living_room`, `bedroom`, `kitchen`, `hallway`, `color_temp` |
| `tv` | 电视 | `status`, `power`, `last_channel`, `volume`, `usage_today`, `source` |

**注意**：注册设备时也可使用自定义 key，不限于上述 4 种。

## 响应格式

### 成功响应

GET 响应示例：
```json
{
  "haolipeng": {
    "air_conditioner": {"status": "on", "mode": "制冷", ...},
    "tv": {"status": "off", "power": "开机", ...}
  }
}
```

PATCH/POST 响应示例：
```json
{"message": "操作成功", "field": "status", "value": "on"}
```

### 错误响应

```json
{"detail": "错误描述信息"}
```

常见错误：
- `404 用户 xxx 不存在`
- `404 用户 xxx 无设备 yyy`
- `409 用户 xxx 已有设备 yyy`（注册时）

## 状态值约定

- `status: "on"` — 设备运行中
- `status: "off"` — 设备关闭

## 组合操作示例

### 场景：晚上睡觉前

```bash
# 1. 关闭客厅电视
curl -s -X PATCH -H "Content-Type: application/json" \
  -d '{"value":"off"}' \
  http://101.34.223.37/api/status/haolipeng/tv/status

# 2. 调高空调温度
curl -s -X PATCH -H "Content-Type: application/json" \
  -d '{"value":"28°C"}' \
  http://101.34.223.37/api/status/haolipeng/air_conditioner/target_temp

# 3. 关闭所有灯（通过 PUT 替换状态）
curl -s -X PUT -H "Content-Type: application/json" \
  -d '{"status":"off","living_room":"关闭","bedroom":"关闭","kitchen":"关闭","hallway":"关闭"}' \
  http://101.34.223.37/api/status/haolipeng/lights
```

### 场景：新设备入网

```bash
# 1. 注册新扫地机器人
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"data":{"status":"off","mode":"自动","battery":"100%"}}' \
  http://101.34.223.37/api/device/haolipeng/robot_vacuum

# 2. 启动它
curl -s -X PATCH -H "Content-Type: application/json" \
  -d '{"value":"on"}' \
  http://101.34.223.37/api/status/haolipeng/robot_vacuum/status
```
