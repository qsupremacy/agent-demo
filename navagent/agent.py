"""
myagent - LangChain Agent with Amap MCP Integration

An agent built using LangChain framework, wrapped with AgentArts SDK runtime.
Supports Amap (高德地图) MCP Server for navigation and location services.

Environment Variables:
    OPENAI_API_KEY: Your OpenAI API key (required)
    OPENAI_BASE_URL: Custom API endpoint URL (optional)
    OPENAI_MODEL_NAME: Model name to use (optional, default: gpt-4o-mini)
    AMAP_API_KEY: Your Amap API key (required for map features)

Configuration:
    Edit .env or .agentarts_config.yaml to customize environment variables.

Usage:
    1. Set your OPENAI_API_KEY and AMAP_API_KEY
    2. Run: agentarts deploy
    3. Invoke: agentarts invoke '{"message": "我想从A地开车去B地"}'
"""

import os
import re
import json
import time
import httpx
import logging
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from dotenv import load_dotenv
from agentarts.sdk.memory import MemoryClient
from agentarts.sdk.memory.inner.config import MemorySearchFilter, TextMessage
from agentarts.sdk import AgentArtsRuntimeApp, RequestContext

# Load environment variables from .env file
load_dotenv()

space_id = os.getenv("AGENTARTS_MEMORY_SPACE_ID")
memory_api_key = os.getenv("HUAWEICLOUD_SDK_MEMORY_API_KEY")


def query_memory(actor_id: str, query: str, cached_session_id: str = None) -> tuple:
    """
    查询用户记忆，返回 (session_id, memories_text)。
    如果传入 cached_session_id 则复用，否则创建新 session。
    memories_text 为拼接好的记忆摘要字符串，可直接注入 system prompt。
    """
    if not space_id or not memory_api_key:
        print("[Memory] 未配置 AGENTARTS_MEMORY_SPACE_ID 或 HUAWEICLOUD_SDK_MEMORY_API_KEY，跳过记忆查询")
        return None, ""

    try:
        with MemoryClient(api_key=memory_api_key) as client:
            # 1. 获取或创建会话
            if cached_session_id:
                session_id = cached_session_id
                print(f"[Memory] 复用已有 Session: {session_id}, actor_id: {actor_id}")
            else:
                session_data = client.create_memory_session(
                    space_id=space_id,
                    actor_id=actor_id,
                )
                session_id = session_data.id
                print(f"[Memory] 创建新 Session: {session_id}, actor_id: {actor_id}")

            # 2. 搜索相关记忆
            start_time = time.time()
            search_results = client.search_memories(
                space_id=space_id,
                filters=MemorySearchFilter(query=query, actor_id=actor_id, top_k=3)
            )
            elapsed = time.time() - start_time

            memories_text = ""
            if search_results and search_results.results and len(search_results.results) > 0:
                print(f"[Memory] 找到 {len(search_results.results)} 条相关记忆, actor_id: {actor_id}, session_id: {session_id}, query: \"{query}\", 耗时: {elapsed:.3f}s")
                memory_lines = []
                for i, mem in enumerate(search_results.results, 1):
                    content = getattr(mem, 'content', None) or getattr(mem, 'memory', None) or str(mem)
                    memory_lines.append(f"  {i}. {content}")
                memories_text = "以下是关于该用户的历史记忆信息：\n" + "\n".join(memory_lines)
            else:
                print(f"[Memory] 未找到相关记忆, actor_id: {actor_id}, session_id: {session_id}, query: \"{query}\", 耗时: {elapsed:.3f}s")

            return session_id, memories_text
    except Exception as e:
        print(f"[Memory] 查询记忆失败: {e}")
        return None, ""


def save_memory(session_id: str, actor_id: str, user_query: str, assistant_response: str):
    """
    将本轮对话的用户消息和助手回复写入记忆库。
    """
    if not space_id or not memory_api_key or not session_id:
        return

    try:
        with MemoryClient(api_key=memory_api_key) as client:
            messages = [
                TextMessage(role="user", content=user_query, actor_id=actor_id),
                TextMessage(role="assistant", content=assistant_response, actor_id=actor_id),
            ]
            client.add_messages(space_id=space_id, session_id=session_id, messages=messages)
            print(f"[Memory] 已存储本轮对话, actor_id: {actor_id}, session_id: {session_id}")
    except Exception as e:
        print(f"[Memory] 存储记忆失败: {e}")

# --- Monkey-patch httpx to log MCP request/response bodies ---
_original_handle_async_request = httpx.AsyncClient.send


def _mask_key(url: str) -> str:
    """将 URL 中的 key 参数匿名化：key=abc123 → key=****"""
    return re.sub(r'(key=)[^&\s]+', r'\1****', url)


class _HttpxKeyMaskFilter(logging.Filter):
    """过滤 httpx 内置日志，匿名化 URL 中的 key 参数。"""
    def filter(self, record):
        if record.args:
            record.args = tuple(
                _mask_key(str(a)) if isinstance(a, str) and "key=" in a else a
                for a in record.args
            )
        record.msg = _mask_key(str(record.msg))
        return True

logging.getLogger("httpx").addFilter(_HttpxKeyMaskFilter())
logging.getLogger("httpcore").addFilter(_HttpxKeyMaskFilter())

async def _patched_send(self, request, *args, **kwargs):
    """Intercept httpx requests to log MCP request/response details."""
    url_str = str(request.url)
    if "mcp.amap.com" in url_str:
        body = request.content
        try:
            body_json = json.loads(body) if body else None
        except (json.JSONDecodeError, TypeError):
            body_json = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)

        body_str = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)

        print(f"\n{'='*60}")
        print(f">>> MCP HTTP REQUEST")
        print(f"    Method: {request.method}")
        print(f"    URL:    {_mask_key(url_str)}")
        print(f"    Headers: {dict(request.headers)}")
        print(f"    Body: {body_str}")
        print(f"{'='*60}")

    response = await _original_handle_async_request(self, request, *args, **kwargs)

    if "mcp.amap.com" in url_str:
        # Read response body without consuming it
        await response.aread()
        resp_body = response.content
        resp_str = resp_body.decode("utf-8", errors="replace") if isinstance(resp_body, bytes) else str(resp_body)
        resp_str = _simplify_mcp_body(resp_str, body_str)

        print(f"\n{'='*60}")
        print(f"<<< MCP HTTP RESPONSE")
        print(f"    Status:  {response.status_code}")
        print(f"    Headers: {dict(response.headers)}")
        print(f"    Body: {resp_str}")
        print(f"{'='*60}")

    return response

httpx.AsyncClient.send = _patched_send
# --- End monkey-patch ---


def _simplify_mcp_body(body_str: str, request_body_str: str = "") -> str:
    """简化 MCP 响应体打印：tools/list 只打印工具名和描述"""
    try:
        data = json.loads(body_str)
        # 检查是否是 tools/list 响应
        if "result" in data and "tools" in data["result"]:
            tools = data["result"]["tools"]
            simplified = [
                {"name": t.get("name", ""), "description": t.get("description", "")[:80]}
                for t in tools
            ]
            return json.dumps({"tools_count": len(tools), "tools": simplified}, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass
    return body_str

app = AgentArtsRuntimeApp()


class AmapMCPClient:
    """Amap MCP client using langchain-mcp-adapters."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
        self._tools = None

    async def initialize(self):
        """Initialize the MCP client and fetch tools."""
        if self._client is not None:
            return

        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
        except ImportError:
            raise ImportError(
                "langchain-mcp-adapters is required. "
                "Install it with: pip install langchain-mcp-adapters"
            )

        self._client = MultiServerMCPClient({
            "amap-maps-streamableHTTP": {
                "url": f"https://mcp.amap.com/mcp?key={self.api_key}",
                "transport": "http"
            },
        })
        self._tools = await self._client.get_tools()

    def get_tools(self) -> List[Any]:
        """Get the list of Amap MCP tools."""
        return self._tools or []

    async def close(self):
        """Close the MCP client."""
        if self._client:
            await self._client.close()
        self._client = None
        self._tools = None


class LangChainAgent:
    """LangChain-based Agent implementation with Amap MCP support."""

    def __init__(self):
        self.name = "myagent"
        self.model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")
        self.amap_api_key = os.environ.get("AMAP_API_KEY")
        self._llm = None
        self._amap_client = None
        self._amap_tools = None
        # 内存会话历史：{actor_id: deque([(user_msg, assistant_msg), ...], maxlen=10)}
        self._history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10))
        # Memory session 缓存：{actor_id: session_id}，同一用户复用同一 session
        self._sessions: Dict[str, str] = {}

    def _get_llm(self):
        """Initialize LLM."""
        if self._llm is None:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable is not set. "
                    "Please set it in .env or .agentarts_config.yaml"
                )

            base_url = os.environ.get("OPENAI_BASE_URL")

            try:
                from langchain_openai import ChatOpenAI
                llm_kwargs = {"model": self.model_name, "api_key": api_key}
                if base_url:
                    llm_kwargs["base_url"] = base_url
                self._llm = ChatOpenAI(**llm_kwargs)
            except ImportError:
                raise ImportError(
                    "langchain-openai is required. Install it with: pip install langchain-openai"
                )
        return self._llm

    async def _get_amap_tools(self) -> List[Any]:
        """Get or create Amap MCP tools."""
        if self._amap_tools is None and self.amap_api_key:
            client = AmapMCPClient(self.amap_api_key)
            await client.initialize()
            self._amap_tools = client.get_tools()
            print(f"\n{'='*60}\nAvailable Amap MCP Tools: {[t.name for t in self._amap_tools]}\n{'='*60}\n")
        return self._amap_tools or []

    async def run(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        actor_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Process a query using LangChain with Amap MCP tools.

        Args:
            query: User input query
            system_prompt: Optional system prompt
            actor_id: Optional user identifier for memory
            **kwargs: Additional parameters

        Returns:
            Response dictionary
        """
        from langchain_core.messages import HumanMessage, AIMessage
        from langchain.agents import create_agent

        llm = self._get_llm()
        amap_tools = await self._get_amap_tools()

        # --- 记忆检索 ---
        session_id = None
        memories_text = ""
        if actor_id:
            cached_session_id = self._sessions.get(actor_id)
            session_id, memories_text = query_memory(actor_id, query, cached_session_id)
            if session_id:
                self._sessions[actor_id] = session_id

        # Build system prompt
        base_system = system_prompt or """你是一个专业的出行助手，可以调用高德地图工具为用户提供路线规划和位置查询服务。

重要规则：
1. 当用户询问路线、导航、怎么去、如何到达时，必须调用 maps_direction_driving（驾车）、maps_direction_transit（公交）、maps_direction_walking（步行）或 maps_direction_bicycling（骑行）工具来获取详细路线。
2. 如果用户未提供起点坐标，先用 maps_geocode 或 maps_search_around 获取起点坐标，再调用路线规划工具。
3. 必须向用户展示详细的路线信息，包括：预计时间、距离、途经道路等，不能只返回高德跳转链接。
4. 如果用户未指定出行方式，默认使用驾车（maps_direction_driving），并询问是否需要其他方式。"""
        if memories_text:
            effective_system = f"{base_system}\n\n{memories_text}\n\n请结合以上用户历史信息来回答问题。"
        else:
            effective_system = base_system

        # --- 构建消息列表（含历史会话）---
        messages = []
        if actor_id:
            history = self._history[actor_id]
            if history:
                print(f"[History] 加载 {len(history)} 轮历史对话 (actor_id: {actor_id})")
                for user_msg, assistant_msg in history:
                    messages.append(HumanMessage(content=user_msg))
                    messages.append(AIMessage(content=assistant_msg))
        messages.append(HumanMessage(content=query))

        # Create agent with Amap tools
        agent = create_agent(
            model=llm,
            tools=amap_tools,
            system_prompt=effective_system
        )

        # Invoke agent
        result = await agent.ainvoke(
            input={"messages": messages}
        )

        # Extract response from result messages
        response_content = ""
        for msg in result.get('messages', []):
            if hasattr(msg, 'content') and msg.content:
                response_content = msg.content

        # Remove LangChain think tags for debug print
        debug_content = re.sub(r'<think>.*?</think>', '', response_content, flags=re.DOTALL).strip()
        print(f"\n{'='*60}\n{debug_content}\n{'='*60}\n")

        # --- 保存本轮到内存历史 ---
        if actor_id:
            self._history[actor_id].append((query, response_content))
            print(f"[History] 已保存本轮对话 \"{query}\"，当前共 {len(self._history[actor_id])} 轮 (actor_id: {actor_id})")

        # --- 记忆存储 ---
        if actor_id and session_id:
            save_memory(session_id, actor_id, query, response_content)

        return {
            "response": response_content,
            "status": "success",
            "agent": self.name,
            "model": self.model_name,
            "actor_id": actor_id,
        }


_agent: Optional[LangChainAgent] = None


def _get_agent() -> LangChainAgent:
    """Get or create the agent instance."""
    global _agent
    if _agent is None:
        _agent = LangChainAgent()
    return _agent


@app.entrypoint
async def handler(payload: Dict[str, Any], context: RequestContext = None) -> Dict[str, Any]:
    """
    Process a query using LangChain with Amap MCP tools.

    Args:
        payload: User input payload containing:
            - message: User query (required)
            - system_prompt: Optional system prompt
            - actor_id: Optional user identifier for memory (default: "default_user")
        context: Request context with session info (optional)

    Returns:
        Response dictionary
    """
    query = payload.get("message", "")
    system_prompt = payload.get("system_prompt")
    actor_id = payload.get("actor_id", "default_user")

    agent = _get_agent()
    return await agent.run(query, system_prompt=system_prompt, actor_id=actor_id)


if __name__ == "__main__":
    app.run()
