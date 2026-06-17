# NavAgent - 高德地图导航智能体

基于 LangChain + AgentArts SDK 构建的智能导航助手，集成高德地图 MCP Server，支持路线规划、位置查询等功能，具备长期记忆与多轮对话能力。

## 功能特性

- **高德地图 MCP 集成**：通过 MCP 协议调用 15 种高德地图工具（驾车/骑行/步行/公交路线规划、POI 搜索、地理编码、天气查询等）
- **长期记忆**：基于华为云 Memory SDK，按用户维度（actor_id）存储对话历史，实现跨会话记忆，session 自动缓存复用
- **多轮对话历史**：每用户最多保留 10 轮对话，超出自动老化淘汰（FIFO）
- **调试日志**：MCP 请求/响应全链路日志，API Key 自动脱敏，tools/list 响应自动简化
- **多模型兼容**：支持 OpenAI 及任何 OpenAI 兼容 API（MiniMax、Azure OpenAI、本地 LLM 等）

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                    AgentArts Runtime                     │
│              (FastAPI + Uvicorn :8080)                   │
└────────────────────────┬────────────────────────────────┘
                         │ POST /invocations
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   handler(payload)                       │
│        提取 message / system_prompt / actor_id           │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  LangChainAgent.run()                    │
│                                                          │
│  1. 记忆检索 ──► MemoryClient.search_memories()         │
│     (session 缓存复用，同一用户不重复创建)               │
│  2. 加载历史 ──► deque(maxlen=10)                        │
│  3. 构建 Prompt ──► system + memories + history          │
│  4. 调用 Agent ──► create_agent() + ainvoke()            │
│  5. 高德 MCP ──► mcp.amap.com (HTTP Streamable)         │
│  6. 保存历史 ──► deque.append()                          │
│  7. 写入记忆 ──► MemoryClient.add_messages()            │
└─────────────────────────────────────────────────────────┘
```

## 可用的高德地图工具

| 工具名 | 说明 |
|--------|------|
| `maps_direction_driving` | 驾车路径规划 |
| `maps_direction_bicycling` | 骑行路径规划（500km 以内） |
| `maps_direction_walking` | 步行路径规划（100km 以内） |
| `maps_direction_transit_integrated` | 公交/地铁/火车综合路径规划 |
| `maps_geo` | 地址 → 经纬度坐标（地理编码） |
| `maps_regeocode` | 经纬度 → 行政区划地址（逆地理编码） |
| `maps_ip_location` | IP 定位 |
| `maps_text_search` | 关键词 POI 搜索 |
| `maps_around_search` | 周边 POI 搜索 |
| `maps_search_detail` | POI 详情查询 |
| `maps_distance` | 距离测量（驾车/步行/直线） |
| `maps_weather` | 天气查询 |
| `maps_schema_navi` | 生成高德 APP 导航唤醒链接 |
| `maps_schema_take_taxi` | 生成高德 APP 打车唤醒链接 |
| `maps_schema_personal_map` | 行程规划地图小程序链接 |

## 前置条件

- Python 3.10+
- OpenAI API Key 或兼容 API 凭证
- 高德地图 API Key（[申请地址](https://lbs.amap.com/)）
- （可选）华为云 Memory SDK 凭证

## 安装

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 依赖包

| 包名 | 用途 |
|------|------|
| `agentarts-sdk` | AgentArts 运行时 SDK + Memory SDK |
| `langchain` | Agent 框架（LangGraph） |
| `langchain-openai` | OpenAI 模型集成 |
| `langchain-core` | LangChain 核心消息类型 |
| `langchain-mcp-adapters` | MCP 协议适配器 |
| `python-dotenv` | 环境变量管理 |
| `httpx` | HTTP 客户端（MCP 通信 + 日志拦截） |

## 配置

### 环境变量

在 `.env` 文件或 `.agentarts_config.yaml` 中配置：

| 变量名 | 必需 | 说明 |
|--------|:----:|------|
| `OPENAI_API_KEY` | ✅ | OpenAI API Key |
| `OPENAI_BASE_URL` | | 自定义 API 端点（用于兼容 API） |
| `OPENAI_MODEL_NAME` | | 模型名称，默认 `gpt-4o-mini` |
| `AMAP_API_KEY` | ✅ | 高德地图 API Key |
| `AGENTARTS_MEMORY_SPACE_ID` | | 记忆空间 ID（可选） |
| `HUAWEICLOUD_SDK_MEMORY_API_KEY` | | 华为云 Memory API Key（可选） |

### 配置示例（.agentarts_config.yaml）

```yaml
runtime:
  environment_variables:
    - key: OPENAI_API_KEY
      value: "sk-xxx"
    - key: OPENAI_MODEL_NAME
      value: "minimax-m2.5"
    - key: OPENAI_BASE_URL
      value: "https://api.minimaxi.com/v1"
    - key: AMAP_API_KEY
      value: "your_amap_key"
    - key: AGENTARTS_MEMORY_SPACE_ID
      value: "your_space_id"
    - key: HUAWEICLOUD_SDK_MEMORY_API_KEY
      value: "your_memory_api_key"
```

## 使用

### 本地开发

```bash
# 启动开发服务器（端口 8080）
agentarts dev
```

### 部署

```bash
# 部署到 AgentArts 平台
agentarts deploy
```

### 调用

```bash
# 使用 CLI 调用
agentarts invoke '{"message": "从上海闵行去人民广场怎么走", "actor_id": "user_123"}'

# 或通过 HTTP 请求
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "message": "从上海闵行去人民广场怎么走",
    "actor_id": "user_123"
  }'
```

## API 参考

### 请求格式

```json
{
  "message": "用户问题（必需）",
  "system_prompt": "自定义系统提示词（可选）",
  "actor_id": "用户标识（可选，默认 default_user）"
}
```

### 响应格式

```json
{
  "response": "助手回复内容",
  "status": "success",
  "agent": "myagent",
  "model": "minimax-m2.5",
  "actor_id": "user_123"
}
```

## 项目结构

```
navagent/
├── agent.py                 # 主程序：Agent + MCP + 记忆 + 会话历史
├── nav.py                   # 独立测试脚本（非服务化）
├── run_agent.py             # Agent 运行脚本
├── run_agent_local.py       # 本地运行脚本
├── requirements.txt         # Python 依赖
├── Dockerfile               # Docker 构建文件
├── README.md                # 项目文档
├── report.md                # 测试报告
├── report_local.md          # 本地测试报告
└── .agentarts_config.yaml   # AgentArts 配置
```

## 核心模块说明

### agent.py 主要组件

| 组件 | 说明 |
|------|------|
| `query_memory()` | 查询华为云 Memory SDK，支持 session 复用 |
| `save_memory()` | 将当前对话写入记忆库 |
| `_simplify_mcp_body()` | 简化 tools/list 响应日志 |
| `_mask_key()` | API Key 脱敏（正则替换 `key=***` → `key=****`） |
| `_HttpxKeyMaskFilter` | httpx/httpcore 内置日志过滤器 |
| `_patched_send()` | httpx 拦截器，打印 MCP 请求/响应日志 |
| `AmapMCPClient` | 高德地图 MCP 客户端封装 |
| `LangChainAgent` | 核心 Agent，整合 LLM + 工具 + 记忆 + 历史 |
| `handler()` | AgentArts 入口点（`@app.entrypoint`） |

### 记忆系统

```
同一用户多轮对话的 session 管理：

请求 1 (actor_id: user_123)
  ├─ _sessions 无缓存 → create_memory_session() → session_AAA
  ├─ search_memories()
  └─ add_messages(session_id=session_AAA)
  → self._sessions["user_123"] = "session_AAA"

请求 2 (actor_id: user_123)
  ├─ _sessions 有缓存 → 复用 session_AAA
  ├─ search_memories()
  └─ add_messages(session_id=session_AAA)

请求 N ...（同一 session 持续复用）
```

## 调试日志

启用后会在控制台输出：

```
============================================================
>>> MCP HTTP REQUEST
    Method: POST
    URL:    https://mcp.amap.com/mcp?key=****
    Headers: {'content-type': 'application/json', ...}
    Body: {"method":"tools/call","jsonrpc":"2.0","params":{"name":"maps_geo",...}}
============================================================

============================================================
<<< MCP HTTP RESPONSE
    Status:  200
    Headers: {'content-type': 'application/json', ...}
    Body: {"jsonrpc":"2.0","result":{"content":[{"type":"text","text":"..."}]}}
============================================================

[Memory] 复用已有 Session: aaa-bbb, actor_id: user_123
[Memory] 找到 3 条相关记忆, actor_id: user_123, session_id: aaa-bbb, query: "去人民广场", 耗时: 0.632s
[History] 加载 5 轮历史对话 (actor_id: user_123)
[History] 已保存本轮对话 "去人民广场怎么走"，当前共 6 轮 (actor_id: user_123)
[Memory] 已存储本轮对话, actor_id: user_123, session_id: aaa-bbb
```

**tools/list 响应自动简化**：

```
<<< MCP HTTP RESPONSE
    Status:  200
    Body: {
      "tools_count": 15,
      "tools": [
        {"name": "maps_direction_driving", "description": "驾车路径规划 API 可以根据用户起终点经纬度坐标规划..."},
        {"name": "maps_geo", "description": "将详细的结构化地址转换为经纬度坐标..."},
        ...
      ]
    }
```

## 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `OPENAI_API_KEY environment variable is not set` | 未配置 API Key | 在 `.env` 或 `.agentarts_config.yaml` 中设置 |
| `langchain-mcp-adapters is required` | 缺少依赖 | `pip install langchain-mcp-adapters` |
| MCP 请求超时 | 网络问题或高德服务异常 | 检查网络连接和高德 API Key |
| 记忆查询失败 | Memory SDK 配置错误 | 检查 `AGENTARTS_MEMORY_SPACE_ID` 和 API Key |
| Agent 只返回导航链接不返回路线 | LLM 未调用路线规划工具 | 已内置强化 system prompt，确保调用 `maps_direction_*` 工具 |
| PyTorch not found 警告 | 非必需依赖 | 可忽略，不影响运行 |

## License

MIT
