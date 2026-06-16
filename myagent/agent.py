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
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from agentarts.sdk import AgentArtsRuntimeApp, RequestContext

# Load environment variables from .env file
load_dotenv()

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
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Process a query using LangChain with Amap MCP tools.

        Args:
            query: User input query
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            Response dictionary
        """
        from langchain_core.messages import HumanMessage
        from langchain.agents import create_agent

        llm = self._get_llm()
        amap_tools = await self._get_amap_tools()

        # Build system prompt
        effective_system = system_prompt or "你是一个专业的出行助手，可以调用高德地图工具为用户提供路线规划和位置查询服务。"

        # Create agent with Amap tools
        agent = create_agent(
            model=llm,
            tools=amap_tools,
            system_prompt=effective_system
        )

        # Invoke agent
        result = await agent.ainvoke(
            input={
                "messages": [HumanMessage(content=query)]
            }
        )

        # Extract response from result messages
        response_content = ""
        for msg in result.get('messages', []):
            if hasattr(msg, 'content') and msg.content:
                response_content = msg.content

        # Remove LangChain think tags for debug print
        import re
        debug_content = re.sub(r'<think>.*?</think>', '', response_content, flags=re.DOTALL).strip()
        print(f"\n{'='*60}\n{debug_content}\n{'='*60}\n")

        return {
            "response": response_content,
            "status": "success",
            "agent": self.name,
            "model": self.model_name,
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
        context: Request context with session info (optional)

    Returns:
        Response dictionary
    """
    query = payload.get("message", "")
    system_prompt = payload.get("system_prompt")

    agent = _get_agent()
    return await agent.run(query, system_prompt=system_prompt)


if __name__ == "__main__":
    app.run()
