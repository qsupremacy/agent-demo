# XXX 内部摸底报告

## 沙箱空载测试

| 对比项       | aws-agentcore | volc-agentkit   | aliyun-agentrun   |
|------      |------------   |----------- | ----------- |
|热请求      |500 ~ 800 ms   | 1000-1100 ms | 1026 ms |
|冷请求      |7400 ~ 8000 ms   | ~5300 ms | 2-3 秒 |
|举证     |[link](https://github.com/qsupremacy/aws-demo/blob/main/awsagent/log_analysis_report.md)  |[link](https://github.com/qsupremacy/volc-demo/blob/main/volcagent/log_analysis_report.md) | [link](https://github.com/qsupremacy/aliyun-demo/blob/main/agentrun/log-analysis-report.md) |

## memory相关测试
| 对比项       | aws-agentmemory | volc-agentkit   | aliyun-agentrun   |
|------      |------------   |----------- | ----------- |
|写请求      |/   | 0.048s | / |
|读请求      |~0.22s   | 0.213s | / |
|举证     |[link](https://github.com/qsupremacy/aws-demo/blob/main/agentmemory/report-analysis.md)  |[link](https://github.com/qsupremacy/volc-demo/blob/main/volcmemory/report.md) | / |


## claw相关测试
| 对比项      | aws-xxx | volc-xxx   | aliyun-jvsclaw   |
|------      |------------   |----------- | ----------- |
|热请求      |/  | / | ~7.6s |
|冷请求      |/   | / | ~7.6s |
|举证     |/  |/ | [link](https://github.com/qsupremacy/aliyun-demo/blob/main/jvscrew/log_analysis.md) |

