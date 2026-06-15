import os
import random
import threading
import time
from agentarts.sdk.memory.inner.config import MemorySearchFilter
from dotenv import load_dotenv
from agentarts.sdk.memory import MemoryClient
from agentarts.sdk.memory.inner.config import TextMessage

load_dotenv()
space_id = os.getenv("AGENTARTS_MEMORY_SPACE_ID")
api_key = os.getenv("HUAWEICLOUD_SDK_MEMORY_API_KEY")


def client_mode_example():
    """Client 模式完整示例（假设已通过Console创建记忆库，并获取spaceId和api-key）"""
    threads = []  # 用来保存所有线程
    for _ in range(10):
        i = random.randint(0, 100)
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
        
        print("\n添加对话消息...")
        messages = [
            TextMessage(
                role="user",
                content="你好，我想了解机器学习的基础知识",
                actor_id=actor_id
            ),
            TextMessage(
                role="assistant",
                content="机器学习是人工智能的一个分支，主要研究如何让计算机从数据中学习规律。",
                actor_id=actor_id
            )
        ]

        start_time = time.time()
        client.add_messages(
            space_id=space_id,
            session_id=session_id,
            messages=messages
        )
        elapsed = time.time() - start_time
        print(f"消息添加成功，耗时: {elapsed:.3f}s")

        return space_id, session_id


if __name__ == "__main__":
    while True:
        client_mode_example()
        time.sleep(1)

