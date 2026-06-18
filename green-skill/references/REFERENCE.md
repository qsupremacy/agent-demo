# 接口参考文档

## fetch_appliance_status()

异步获取原始家电状态数据。

**参数：** 无

**返回值：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | `str` | `"success"` 或 `"error"` |
| `data` | `dict` | 成功时返回设备状态数据 |
| `error` | `str` | 失败时返回错误描述 |

## format_status_text(data)

将原始 JSON 数据格式化为可读文本。

**参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `data` | `dict` | `fetch_appliance_status()` 返回的 `data` 字段 |

**返回值：** 多行文本字符串

## GreenSkillTool

LangChain 工具封装类。

| 属性 | 值 |
|------|-----|
| `name` | `get_appliance_status` |
| `description` | 获取家庭家电实时状态，包括空调、冰箱、灯具、电视的运行信息 |

**方法：**

- `async arun(query: str) -> str` — 异步调用
- `run(query: str) -> str` — 同步调用

## 错误码

| 错误类型 | 返回信息 |
|----------|----------|
| 请求超时 | `请求超时，远程服务无响应` |
| HTTP 错误 | `HTTP 错误: <状态码>` |
| 格式异常 | `远程返回数据格式异常` |
| 其他异常 | `获取失败: <异常详情>` |
