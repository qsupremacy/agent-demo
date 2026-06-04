# 内存组件测试

## 核心逻辑

```
while True:
    └── 启动 100 个线程并发查询
        └── query_memory(actor_id)
            ├── 创建会话 (create_memory_session)
            ├── 查询记忆列表 (list_memories)
            └── 搜索记忆 (search_memories)
    └── 等待 100 线程完成
    └── sleep(1)
```

## 流程特点

- 每个 actor_id 随机生成（0~1000），可能重复
- 每个线程独立创建 `MemoryClient` 连接
- 所有 100 线程并发执行后，主线程才继续

## 推断意图

本意是纯查询，但代码保留了创建会话逻辑，可能是为了先确保会话存在再查询。



