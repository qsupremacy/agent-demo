import os
import random
import threading
import time
from agentarts.sdk.memory import MemoryClient
from agentarts.sdk.memory.inner.config import MemorySearchFilter
from dotenv import load_dotenv

load_dotenv()
space_id = os.getenv("AGENTARTS_MEMORY_SPACE_ID")
api_key = os.getenv("HUAWEICLOUD_SDK_MEMORY_API_KEY")


def client_mode_example():
    """Client 模式完整示例（假设已通过Console创建记忆库，并获取spaceId和api-key）"""
    threads = []  # 用来保存所有线程
    for _ in range(100):
        i = random.randint(0, 1000)
        actor_id = "user-" + str(i)
        t=threading.Thread(
            target=query_memory,
            args=(actor_id,),
            daemon=True
        )
        t.start()
        threads.append(t)  # 存起来
    # 🔥 等待所有线程执行完毕
    for t in threads:
        t.join()

    # 这里会等所有 query_memory 跑完才执行！
    print("✅ 所有记忆插入完成！程序退出")
    return


def query_memory(actor_id):
    with MemoryClient(api_key=api_key) as client:
        # 1. 创建会话
        print("\n创建会话...")
        session_data = client.create_memory_session(
            space_id=space_id,
            actor_id=actor_id,
        )
        session_id = session_data.id
        print(f"Session ID: {session_id}")

        # 4. 查询记忆
        print("\n查询记忆列表...")
        memories = client.list_memories(space_id=space_id, limit=10)
        print(f"发现 {len(memories.items)} 条记忆")

        # 5. 搜索记忆
        print("\n搜索相关记忆...")
        search_results = client.search_memories(
            space_id=space_id,
            filters=MemorySearchFilter(query="我的家在哪里", actor_id=actor_id, top_k=3)
        )
        print(f"找到 {len(search_results.results)} 条相关记忆")
        #print(f"内容为： {search_results.results}")

        return space_id, session_id


if __name__ == "__main__":
    while True:
        client_mode_example()
        time.sleep(1)

