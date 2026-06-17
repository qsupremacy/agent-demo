"""
华为云 Memory SDK 封装：查询记忆 + 存储记忆
"""
import time
from agentarts.sdk.memory import MemoryClient
from agentarts.sdk.memory.inner.config import MemorySearchFilter, TextMessage
import config


def query_memory(actor_id: str, query: str, cached_session_id: str = None) -> tuple:
    """
    查询用户记忆，返回 (session_id, memories_text)。
    如果传入 cached_session_id 则复用，否则创建新 session。
    memories_text 为拼接好的记忆摘要字符串，可直接注入 system prompt。
    """
    if not config.MEMORY_SPACE_ID or not config.MEMORY_API_KEY:
        print("[Memory] 未配置 AGENTARTS_MEMORY_SPACE_ID 或 HUAWEICLOUD_SDK_MEMORY_API_KEY，跳过记忆查询")
        return None, ""

    try:
        with MemoryClient(api_key=config.MEMORY_API_KEY) as client:
            # 1. 获取或创建会话
            if cached_session_id:
                session_id = cached_session_id
                print(f"[Memory] 复用已有 Session: {session_id}, actor_id: {actor_id}")
            else:
                session_data = client.create_memory_session(
                    space_id=config.MEMORY_SPACE_ID,
                    actor_id=actor_id,
                )
                session_id = session_data.id
                print(f"[Memory] 创建新 Session: {session_id}, actor_id: {actor_id}")

            # 2. 搜索相关记忆
            start_time = time.time()
            search_results = client.search_memories(
                space_id=config.MEMORY_SPACE_ID,
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
    if not config.MEMORY_SPACE_ID or not config.MEMORY_API_KEY or not session_id:
        return

    try:
        with MemoryClient(api_key=config.MEMORY_API_KEY) as client:
            messages = [
                TextMessage(role="user", content=user_query, actor_id=actor_id),
                TextMessage(role="assistant", content=assistant_response, actor_id=actor_id),
            ]
            client.add_messages(space_id=config.MEMORY_SPACE_ID, session_id=session_id, messages=messages)
            print(f"[Memory] 已存储本轮对话, actor_id: {actor_id}, session_id: {session_id}")
    except Exception as e:
        print(f"[Memory] 存储记忆失败: {e}")
