# XXX 内部摸底报告

## 沙箱空载测试

| 对比项       | aws-agentcore | volc-agentkit   | aliyun-agentrun   | agent-demo
|------      |------------    |-----------   | ----------- | ---------- |
|热请求      |500 ~ 800 ms     | 1000-1100 ms | 1026 ms     | 2.5s |
|冷请求      |7400 ~ 8000 ms   | ~5300 ms     | 2-3 秒      | >15s |
|举证        |[link](https://github.com/qsupremacy/aws-demo/blob/main/awsagent/log_analysis_report.md)  | [link](https://github.com/qsupremacy/volc-demo/blob/main/volcagent/log_analysis_report.md) | [link](https://github.com/qsupremacy/aliyun-demo/blob/main/agentrun/log-analysis-report.md) | [link](https://github.com/qsupremacy/agent-demo/blob/main/agents/report.md) |

## memory相关测试
| 对比项       | aws-agentmemory | volc-agentkit   | aliyun-agentrun   | agent-demo|
|------      |------------   |----------- | ----------- | -----------------|
|写请求      |/              | 0.048s      | /          | 0.05s  |
|读请求      |~0.22s         | 0.213s |      /          | 0.608s |
|举证     |[link](https://github.com/qsupremacy/aws-demo/blob/main/agentmemory/report-analysis.md)  |[link](https://github.com/qsupremacy/volc-demo/blob/main/volcmemory/report.md) | / | [link](https://github.com/qsupremacy/agent-demo/blob/main/memory/logs_summary.md) |


## claw相关测试
| 对比项      | aws-xxx | volc-xxx   | aliyun-jvsclaw   | agent-demo |
|------      |------------   |----------- | ----------- |----------- |
|热请求      |/              | /          | ~7.6s       | 10s|
|冷请求      |/              | /          | ~7.6s       | 1min01s|
|举证        |/              |/           | [link](https://github.com/qsupremacy/aliyun-demo/blob/main/jvscrew/log_analysis.md) | / |


## 附录
### 第1次
```
default
思考执行完成（已调用0个工具，耗时1m01s）
你好！👋
我是你的安全专家助手，随时准备帮助你处理安全相关的问题。
有什么我可以帮你的吗？无论是安全咨询、风险评估、还是其他安全相关的需求，都可以告诉我。
06/16 10:50
```
### 第2次
```
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
### 第3次
```
default
思考执行完成（已调用0个工具，耗时9s）
你好！我在这里，随时待命。有什么问题或需求请直接告诉我
```

