## 节点数据

| 节点 | 请求数 | 平均耗时 | 错误数 |
|------|--------|----------|--------|
| `/*(memory.cn-southwest-2.huaweicloud-agentarts.com)` | 21,337 | 1596ms | 2,587 |
| `agentarts-memory` | 0 | 0ms | 0 |

## 关键指标

- **QPS**: 约 21,337 次请求
- **平均响应时间**: 1596ms (1.6秒) - 较慢
- **错误率**: 2587/21337 ≈ **12.1%** - 错误率偏高
- **拓扑关系**: `agentarts-memory` 服务触发 HTTP 调用到云端

## 问题点

1. 12% 错误率需要排查
2. 1.6秒平均响应时间较长，可能存在性能瓶颈
3. `agentarts-memory` 节点显示 0 请求，说明监控数据可能只统计了出口层

## 错误信息示例
```
2026-06-04 15:17:49,299 - agentarts.sdk.memory.inner.dataplane - INFO - DataPlane closed
Exception in thread Thread-2797 (insert_memory):
Traceback (most recent call last):
  File "/usr/lib/python3.12/threading.py", line 1073, in _bootstrap_inner
    self.run()
  File "/home/ubuntu/openclaw-viewer/.venv/lib/python3.12/site-packages/opentelemetry/instrumentation/threading/__init__.py", line 152, in __wrap_threading_run
    return call_wrapped(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/threading.py", line 1010, in run
    self._target(*self._args, **self._kwargs)
  File "/home/ubuntu/workspace/query.py", line 49, in insert_memory
    memories = client.list_memories(space_id=space_id, limit=10)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/openclaw-viewer/.venv/lib/python3.12/site-packages/agentarts/sdk/memory/client.py", line 884, in list_memories
    return self._data_plane.list_memories(space_id, limit, offset, filters)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/openclaw-viewer/.venv/lib/python3.12/site-packages/agentarts/sdk/memory/inner/dataplane.py", line 257, in list_memories
    result = self.client.list_memories(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/openclaw-viewer/.venv/lib/python3.12/site-packages/agentarts/sdk/service/memory_service.py", line 667, in list_memories
    return self._make_request(method="GET", path=f"/v1/core/spaces/{space_id}/memories", params=params,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ubuntu/openclaw-viewer/.venv/lib/python3.12/site-packages/agentarts/sdk/service/memory_service.py", line 352, in _make_request
    raise MemoryAPIException(
agentarts.sdk.service.memory_service.MemoryAPIException: [APIG.0203] HTTP 504: Backend timeout
```
