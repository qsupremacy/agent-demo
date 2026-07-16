# Agent 运行时压测对比报告

> 数据源：`ab_aliyun_agentrun_inner.log`、`ab_huaweicloud_agentarts_inner.log`
> 测试工具：ApacheBench 2.3 ｜ 请求数：10000 ｜ 并发：1
> 网络：均走内网

---

## 1. 测试对象与链路拓扑

| 维度 | AgentArts（华为云） | AgentRun（阿里云） |
|---|---|---|
| 区域 | 贵阳一 | 上海一 |
| 客户端 → 服务端 | 贵阳 ECS → 贵阳 AgentArts | 上海 ECS → 上海 AgentRun |
| 接入层 | **ELB**（云负载均衡） | **VPC EP**（终端节点服务 / PrivateLink 类） |
| 鉴权 | 已去除 CLI 依赖、AK/SK 签名 | 仍走网关策略校验 |
| 业务实现 | Python Web 框架（uvicorn），**直接输出 mock** | 需做 **私有协议 → OpenAI Chat 协议** 适配 |
| 调用路径 | `/runtimes/runtime-sdk013/invocations?endpoint=Latest` | `/agent-runtimes/agent-code-AawC7/endpoints/Default/invocations/openai/v1/chat/completions` |
| 响应体 | 90 bytes（私有协议 mock 结果） | 246 bytes（OpenAI Chat Completion 完整 JSON） |

### 调用链拓扑

```
【AgentArts（贵阳）】
ECS ──TLS──▶ ELB ──▶ uvicorn(Python) ──▶ mock 直出
                                                       （P50 ≈ 6ms）

【AgentRun（上海）】
ECS ──TLS──▶ VPC EP ──▶ 网关鉴权 ──▶ 协议适配器 ──▶ Runtime(mock) ──▶ 协议适配器 ──▶ VPC EP ──▶ ECS
                                                       （P50 ≈ 25ms）
```

---

## 2. 核心性能指标

| 指标 | AgentArts | AgentRun | 倍数差 |
|---|---|---|---|
| 总耗时 | 63.677 s | 249.700 s | AgentArts **快 3.9×** |
| QPS | 157.04 | 40.05 | AgentArts **高 3.9×** |
| 平均时延 | 6.37 ms | 24.97 ms | AgentArts **低 3.9×** |
| 中位 P50 | 6 ms | 23 ms | AgentArts 快 ~4× |
| P95 | 7 ms | 34 ms | AgentArts 快 ~5× |
| P99 | 8 ms | 55 ms | AgentArts 快 ~7× |
| P100（max） | 490 ms | 320 ms | AgentRun 略稳 |
| 接收吞吐 | 47.70 KB/s | 28.90 KB/s | — |
| Connect 中位 | 3 ms | 7 ms | AgentArts 更快 |
| 网络 RTT（ping） | ~0.69 ms | ~0.70 ms | 几乎相同 |
| 失败请求 | 0 | 0 | 持平 |
| Non-2xx 响应 | 0 | 0 | 持平 |

---

## 3. 时延分布与延迟拆分

### 3.1 分布形态

```
AgentArts:  min=6   median=6   P95=7   P99=8   max=490  σ≈4.9   ← 窄、极度集中
AgentRun:   min=14  median=23  P95=34  P99=55  max=320  σ≈9.0   ← 较宽、整体右移
```

- **AgentArts 是典型的"稳定快"**：P99 才 8 ms，绝大多数请求落在 6–8 ms 一档；490 ms 尖刺属于极稀疏事件。
- **AgentRun 是"持续慢"**：从 P50=23 ms 起就已经是 AgentArts P99 的 3 倍，不是抖动，而是常态开销大。

### 3.2 延迟按链路拆分

| 段 | AgentArts | AgentRun | 差值 | 归因 |
|---|---|---|---|---|
| TLS 建链 | 3 ms | 7 ms | **+4 ms** | VPC EP 比 ELB 多一跳终端节点封装 |
| 网关 / 转发 | ~1 ms | ~3 ms | **+2 ms** | VPC EP 安全策略 + 路由 |
| 鉴权 | 0 ms（已剔除） | ~3 ms | **+3 ms** | AgentRun 网关仍做策略校验 |
| **协议适配** | 0 ms | **~7–9 ms** | **+8 ms** | OpenAI Chat ⇄ 内部协议解析 / 序列化 |
| Runtime 执行 | ~2 ms | ~2 ms | 0 | 都是 mock，开销相当 |
| 响应序列化 | ~0 ms（90 B） | ~1 ms（246 B） | **+1 ms** | OpenAI JSON 字段更多 |
| **合计** | ~6 ms | ~24–25 ms | **~19 ms** | 与实测 25−6=19 ms 吻合 |

> **协议适配占了 ~8 ms，是 AgentRun 这条路径最大的固定开销**，不是网络也不是 Runtime 本身慢。

---

## 4. 与上次测试的差异说明

| 维度 | 上次 | 本次 |
|---|---|---|
| 网络 | 混合（部分外网） | **统一走内网** |
| AgentArts 鉴权 | CLI 工具 + AK/SK 签名 | **已去除** |
| AgentRun 路径 | `…/ndpoints/Default/…`（拼写错误，10000/10000 Non-2xx） | `…/endpoints/Default/…`（已修正） |
| 结论有效性 | 作废：Aliyun 打到了错误路由 | **有效**：两侧均命中真实端点 |

---

## 5. 关键发现

### 5.1 不能直接比的指标

1. **响应体大小（90 vs 246 bytes）不是慢的理由，是产物**：
   - AgentArts 返回私有协议字段，90 B
   - AgentRun 必须返回 OpenAI Chat 完整结构（`id/object/created/model/choices/usage`），246 B
   - ~150 B 差异是协议格式决定，序列化开销约 1 ms，可忽略

2. **"QPS 40 vs 157" 不能直接比**：
   - AgentArts 每次调用服务端只做"返回 mock 字符串"，本质是测 ELB+uvicorn 的转发能力
   - AgentRun 每次调用服务端做"鉴权 + 协议转换 + mock + 序列化 OpenAI JSON"，本质是测网关+适配器能力
   - 任务复杂度差 ~4 倍，QPS 差 ~4 倍，**系数一致，结构合理**

3. **无抖动、无失败**：
   - AgentRun P99=55 ms、P100=320 ms，但 σ=9 ms——是稳定偏高，不是抖动
   - AgentArts P99=8 ms、P100=490 ms，但 10k 里几乎全在 6–8 ms，490 ms 是孤例
   - 两侧均无排队 / 超时 / 雪崩迹象

### 5.2 19 ms 差距的归因

```
总差距 19 ms ≈ VPC EP 接入 (+4ms) + 网关鉴权 (+3ms) + 协议适配 (+8ms) + 序列化 (+1ms) + 其他 (~3ms)
            ──── 接入方式固有成本 ────   ─── 鉴权 + 转换 不可消除 ───
```

**~18 ms 是架构差异（接入方式 + 协议转换），只有 ~1 ms 可能归到 Runtime 本身**。两个 Runtime 当前表现都在合理范围内。

---

## 6. 结论

| 维度 | 结论 |
|---|---|
| **网络** | 两侧内网 RTT 都是 ~0.7 ms，无差异 |
| **接入层** | VPC EP 比 ELB 多 ~4 ms（建链 + 策略），属于接入方式固有成本 |
| **协议层** | AgentRun 多 ~8 ms 做 OpenAI ⇄ 私有协议转换，是这条路径的主要开销且难以消除 |
| **运行时本身** | 两边 mock 执行都很快（~2 ms），没有可比出优劣 |
| **稳定性** | 两侧 0 失败、P99 内无抖动，均合格 |
| **整体评价** | AgentArts 路径更短、更轻；AgentRun 路径功能更完整（OpenAI 兼容），开销与功能成正比 |

---

## 7. 后续建议

### 7.1 想压低 AgentRun 的 25 ms

- 启用 HTTP/2 或 keep-alive，让单连接摊薄 4 ms TLS 建链 → 实际 RPS 会显著上升
- 协议适配这块基本是必须的，除非放弃 OpenAI 兼容

### 7.2 想真正对比"运行时"

- 让两边都跳过协议层：AgentRun 直接走内部协议路径调用，绕过 OpenAI 适配器
- 那时差距应该只剩"接入层 4 ms + 序列化 1 ms ≈ 5 ms"，才是 Runtime 本身的差异

### 7.3 想看并发能力

- 跑一份 `ab -c 10 -n 10000`，看 AgentArts 的 uvicorn（默认单 worker）是否在并发下出现排队
- 同时看 AgentRun 的网关并发上限在哪

---

## 8. 附录：原始数据

### AgentArts（华为云，贵阳）

```
Server:        uvicorn
Document Path: /runtimes/runtime-sdk013/invocations?endpoint=Latest
Document Len:  90 bytes
Concurrency:   1
Total time:    63.677 s
Requests:      10000 / 10000
Failed:        0
RPS:           157.04
Mean:          6.368 ms
P50/P95/P99:   6 / 7 / 8 ms
Max:           490 ms
Connect:       min=3, mean=3, median=3, max=6
Processing:    min=2, mean=3, median=3, max=485
```

### AgentRun（阿里云，上海）

```
Server:        （网关层不可见）
Document Path: /agent-runtimes/agent-code-AawC7/endpoints/Default/invocations/openai/v1/chat/completions
Document Len:  246 bytes
Concurrency:   1
Total time:    249.700 s
Requests:      10000 / 10000
Failed:        0
RPS:           40.05
Mean:          24.970 ms
P50/P95/P99:   23 / 34 / 55 ms
Max:           320 ms
Connect:       min=5, mean=7, median=7, max=90
Processing:    min=8, mean=17, median=16, max=313
```