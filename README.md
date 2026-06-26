# XXX 内部摸底报告

## 一、沙箱空载测试
### 基本概念
* 冷请求：新用户请求hello，触发拉起新实例，端到端完整返回的耗时  
* 热请求：复用冷请求拉取的实例，请求hello，端到端完整返回的耗时
* XXX(空载)：以上请求使用Langchain框架，但没有调用LLM，收到请求后，直接返回。
* 环境：以下测试均通过公网访问测试，如果走内网耗时会更少

### 实测数据
| 对比项       | aws-agentcore | volc-agentkit   | aliyun-agentrun   | agent-demo
|------       |------------    |-----------   | ----------- | ---------- |
|冷请求(空载)      |7400 ~ 8000 ms   | ~8s(预估)      | ~8s    | >15s |
|热请求(空载)      |500 ~ 800 ms     | <200 ms       | <100 ms       | 2.5s |
|举证              |[link](https://github.com/qsupremacy/aws-demo/blob/main/awsagent/log_analysis_report.md)  | [link](https://github.com/qsupremacy/volc-demo/blob/main/volcagent/same_diff_analysis.md) | [link](https://github.com/qsupremacy/aliyun-demo/blob/main/agentrun/session-modes-report.md) | [link](https://github.com/qsupremacy/agent-demo/blob/main/agents/report.md) |

### 备注
* aws-agentcore 链路上海->新加坡。物理距离较远,aws提供的console测试时延<200ms
* volc-agentkit 链路上海->北京。agentkit是进程级安全隔离，冷请求为估算数据。
* aliyun-agentrun 链路上海->上海。AgentRun默认进程级隔离，支持切换为MicroVM隔离

## 二、memory相关测试
| 对比项       | aws-agentmemory | volc-agentkit   | aliyun-agentrun   | agent-demo|
|------      |------------   |----------- | ----------- | -----------------|
|写请求      |/              | 0.048s      | /          | 0.05s  |
|读请求      |~0.22s         | 0.213s |      /          | 0.608s |
|举证     |[link](https://github.com/qsupremacy/aws-demo/blob/main/agentmemory/report-analysis.md) |[link](https://github.com/qsupremacy/volc-demo/blob/main/volcmemory/report.md) |

## 三、claw相关测试
* 冷请求：新用户、新会话，请求hello，端到端完整返回的耗时  
* 热请求：复用冷请求的会话，请求hello，端到端完整返回的耗时  
* XXX(空载)：以上请求耗时减去LLM调用的时间（LLM的耗时通过平台提供的链路耗时获得）  

| 对比项      | aws-xxx | volc-xxx   | aliyun-jvscrew   | agent-demo |
|------      |------------   |----------- | ----------- |----------- |
|冷请求      |/              | /          | ~7.85s      | 1min01s|
|冷请求(空载)|/              | /          | ~3.1s       | ?|
|热请求      |/              | /          | ~4s         | 10s|
|热请求(空载)|/              | /          | ~1.3s       | ?|
|举证        |/              |/           | [冷，](https://github.com/qsupremacy/aliyun-demo/blob/main/jvscrew/diff_report.md)[热](https://github.com/qsupremacy/aliyun-demo/blob/main/jvscrew/blank20260625_report.md)| / |


## X、附录
### JVSCrew
## 客户端 vs 服务端耗时对比

| Turn | 客户端 (s) | 服务端 (LAUNCH+LLM) (s) | 差值 (网络+其他) (s) |
|------|-----------|------------------------|-------------------|
| 1 | 3.974 | 2.311 | 1.663 |
| 2 | **6.106** | 4.860 | 1.246 |
| 3 | 3.851 | 2.467 | 1.384 |
| 4 | 2.988 | 1.707 | 1.281 |
| 5 | 4.604 | 3.241 | 1.363 |
| 6 | 4.696 | 3.368 | 1.328 |
| 7 | 3.704 | 2.232 | 1.472 |
| 8 | 3.580 | 2.204 | 1.376 |
| 9 | 4.473 | 3.206 | 1.267 |
| 10 | 3.394 | 2.007 | 1.387 |
| **平均** | **4.137** | **2.760** | **1.377** |

### XXXClaw
```### 第1次
default
思考执行完成（已调用0个工具，耗时1m01s）
你好！👋
我是你的安全专家助手，随时准备帮助你处理安全相关的问题。
有什么我可以帮你的吗？无论是安全咨询、风险评估、还是其他安全相关的需求，都可以告诉我。
06/16 10:50
```
```### 第2次
default
思考执行完成（已调用0个工具，耗时13s）
你好！👋
有什么我可以帮你的吗？作为安全专家助手，我可以协助你处理：
安全咨询与建议
风险评估与分析
安全配置审查
漏洞相关讨论
其他安全相关问题
随时告诉我你的需求！
```

```### 第3次
default
思考执行完成（已调用0个工具，耗时9s）
你好！我在这里，随时待命。有什么问题或需求请直接告诉我
```

### 客服答复
```
售后工程师
2026-06-26 10:40:34
开启Header Session会话隔离后时延升至10s属正常现象。因系统为每个会话分配独立实例并强制1:1绑定，首次请求需冷启动（如模型加载、NAS挂载），导致延迟显著上升。基线100ms为无隔离时复用实例的性能，隔离后因资源独占和初始化开销，10s时延符合预期。 详细信息请参考： 函数计算-会话隔离配置
```
