# NavAgent - 高德地图导航智能体

基于 LangChain + AgentArts SDK 构建的智能导航助手，集成高德地图 MCP Server，支持路线规划、位置查询，具备长期记忆与多轮对话能力。

## 项目架构

```
navagent/
├── agent.py        (192行) 核心 Agent：LLM + 高德工具 + 记忆 + 会话历史
├── config.py       (19行)  环境变量配置
├── memory.py       (75行)  华为云 Memory SDK 封装
├── mcp_debug.py    (86行)  MCP 调试日志 + Key 脱敏
├── nav.py          (63行)  独立测试脚本（非服务化）
├── run_agent.py    (26行)  云端运行脚本
├── run_agent_local.py (26行) 本地运行脚本
├── requirements.txt        Python 依赖
├── Dockerfile              Docker 构建文件
└── .agentarts_config.yaml  AgentArts 配置
```

### 模块职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| **config.py** | 集中管理所有环境变量（LLM、高德、Memory） | `dotenv` |
| **memory.py** | `query_memory()` 查询记忆 + `save_memory()` 存储记忆，支持 session 复用 | `agentarts.sdk.memory` |
| **mcp_debug.py** | `setup_mcp_logging()` 启用调试日志，httpx 拦截 + Key 脱敏 + tools/list 简化 | `httpx`, `logging` |
| **agent.py** | `AmapMCPClient` + `LangChainAgent` + `handler()`，纯业务编排 | `config`, `memory`, `mcp_debug` |

## 核心特性

- **高德地图 MCP 集成**：15 种工具（驾车/骑行/步行/公交路线规划、POI 搜索、地理编码、天气查询等）
- **长期记忆**：基于华为云 Memory SDK，按 actor_id 维度存储，session 自动缓存复用
- **多轮对话**：内存历史（deque, maxlen=10）+ 长期记忆双层机制
- **调试日志**：MCP 请求/响应全链路日志，API Key 自动脱敏，tools/list 响应自动简化
- **多模型兼容**：支持 OpenAI 及任何 OpenAI 兼容 API（MiniMax、Azure OpenAI 等）

## 安装

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 依赖包

```
pydantic>=2.10.0
agentarts-sdk
langchain>=0.1.0
langchain-openai>=0.1.0
langchain-core>=0.1.0
langchain-mcp-adapters>=0.1.0
python-dotenv>=1.0.0
```

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

### 云端部署

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

## 记忆系统

### Session 复用机制

```
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

### 双层历史机制

| 层级 | 存储 | 容量 | 用途 |
|------|------|------|------|
| 内存历史 | `deque(maxlen=10)` | 每用户 10 轮 | 短期多轮对话 |
| 长期记忆 | 华为云 Memory SDK | 无限制 | 跨会话记忆 |

## 调试日志

启用后会在控制台输出：

```
[MCP Debug] 已启用 MCP 请求/响应日志，API Key 自动脱敏

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

### tools/list 响应自动简化

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

## Docker 部署

### 构建单架构镜像

```bash
# x86 架构
docker build --platform linux/amd64 -t navagent:amd64 .

# ARM64 架构（x86 机器上交叉编译会较慢，约 5-10 分钟）
docker buildx build --platform linux/arm64 -t navagent:arm64 --load .
```

### 构建双架构镜像并推送

```bash
# 创建 buildx builder
docker buildx create --name multiarch --use

# 构建并推送
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t swr.cn-southwest-2.myhuaweicloud.com/agentarts-org-haolipeng/agent_myagent:latest \
  --push .
```

## 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `OPENAI_API_KEY 未设置` | 未配置 API Key | 在 `.env` 或 `.agentarts_config.yaml` 中设置 |
| `langchain-mcp-adapters is required` | 缺少依赖 | `pip install langchain-mcp-adapters` |
| MCP 请求超时 | 网络问题或高德服务异常 | 检查网络连接和高德 API Key |
| 记忆查询失败 | Memory SDK 配置错误 | 检查 `AGENTARTS_MEMORY_SPACE_ID` 和 API Key |
| Agent 只返回导航链接 | LLM 未调用路线规划工具 | 已内置强化 system prompt，确保调用 `maps_direction_*` 工具 |
| PyTorch not found 警告 | 非必需依赖 | 可忽略，不影响运行 |
| ARM64 构建慢 | QEMU 模拟 | 正常现象，首次构建 5-10 分钟，后续有缓存 |

## License

MIT
