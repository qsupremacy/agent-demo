"""
NavAgent - 高德地图导航智能体

基于 LangChain + AgentArts SDK，集成高德地图 MCP Server，
支持路线规划、位置查询，具备长期记忆与多轮对话能力。
"""
import os
import re
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque

from agentarts.sdk import AgentArtsRuntimeApp, RequestContext

import config
from memory import query_memory, save_memory
from mcp_debug import setup_mcp_logging

# 启用 MCP 调试日志（monkey-patch httpx + Key 脱敏）
setup_mcp_logging()

app = AgentArtsRuntimeApp()


class AmapMCPClient:
    """高德地图 MCP 客户端，基于 langchain-mcp-adapters。"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
        self._tools = None

    async def initialize(self):
        if self._client is not None:
            return
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
        except ImportError:
            raise ImportError("langchain-mcp-adapters is required. pip install langchain-mcp-adapters")

        self._client = MultiServerMCPClient({
            "amap-maps-streamableHTTP": {
                "url": f"https://mcp.amap.com/mcp?key={self.api_key}",
                "transport": "http"
            },
        })
        self._tools = await self._client.get_tools()

    def get_tools(self) -> List[Any]:
        return self._tools or []

    async def close(self):
        if self._client:
            await self._client.close()
        self._client = None
        self._tools = None


DEFAULT_SYSTEM_PROMPT = """你是一个专业的出行助手，可以调用高德地图工具为用户提供路线规划和位置查询服务。

重要规则：
1. 当用户询问路线、导航、怎么去、如何到达时，必须调用 maps_direction_driving（驾车）、maps_direction_transit（公交）、maps_direction_walking（步行）或 maps_direction_bicycling（骑行）工具来获取详细路线。
2. 如果用户未提供起点坐标，先用 maps_geocode 或 maps_search_around 获取起点坐标，再调用路线规划工具。
3. 必须向用户展示详细的路线信息，包括：预计时间、距离、途经道路等，不能只返回高德跳转链接。
4. 如果用户未指定出行方式，默认使用驾车（maps_direction_driving），并询问是否需要其他方式。"""


class LangChainAgent:
    """核心 Agent：LLM + 高德工具 + 记忆 + 会话历史。"""

    def __init__(self):
        self.name = "myagent"
        self.model_name = config.OPENAI_MODEL_NAME
        self._llm = None
        self._amap_tools = None
        self._history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10))
        self._sessions: Dict[str, str] = {}

    def _get_llm(self):
        if self._llm is None:
            if not config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY 未设置，请在 .env 或 .agentarts_config.yaml 中配置")
            try:
                from langchain_openai import ChatOpenAI
                llm_kwargs = {"model": self.model_name, "api_key": config.OPENAI_API_KEY}
                if config.OPENAI_BASE_URL:
                    llm_kwargs["base_url"] = config.OPENAI_BASE_URL
                self._llm = ChatOpenAI(**llm_kwargs)
            except ImportError:
                raise ImportError("langchain-openai is required. pip install langchain-openai")
        return self._llm

    async def _get_amap_tools(self) -> List[Any]:
        if self._amap_tools is None and config.AMAP_API_KEY:
            client = AmapMCPClient(config.AMAP_API_KEY)
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

        # --- 构建 system prompt ---
        base_system = system_prompt or DEFAULT_SYSTEM_PROMPT
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

        # --- 执行 Agent ---
        agent = create_agent(model=llm, tools=amap_tools, system_prompt=effective_system)
        result = await agent.ainvoke(input={"messages": messages})

        # --- 提取响应 ---
        response_content = ""
        for msg in result.get('messages', []):
            if hasattr(msg, 'content') and msg.content:
                response_content = msg.content

        debug_content = re.sub(r'<think>.*?</think>', '', response_content, flags=re.DOTALL).strip()
        print(f"\n{'='*60}\n{debug_content}\n{'='*60}\n")

        # --- 保存历史 + 记忆 ---
        if actor_id:
            self._history[actor_id].append((query, response_content))
            print(f"[History] 已保存本轮对话 \"{query}\"，当前共 {len(self._history[actor_id])} 轮 (actor_id: {actor_id})")

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
    global _agent
    if _agent is None:
        _agent = LangChainAgent()
    return _agent


@app.entrypoint
async def handler(payload: Dict[str, Any], context: RequestContext = None) -> Dict[str, Any]:
    """AgentArts 入口点。"""
    query = payload.get("message", "")
    system_prompt = payload.get("system_prompt")
    actor_id = payload.get("actor_id", "default_user")

    agent = _get_agent()
    return await agent.run(query, system_prompt=system_prompt, actor_id=actor_id)


if __name__ == "__main__":
    app.run()
