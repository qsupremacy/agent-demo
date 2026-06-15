import subprocess
import time
from datetime import datetime

for i in range(1, 10):
    start_time = datetime.now()

    result = subprocess.run(
        f"agentarts invoke '{{\"message\": \"Hello World\"}}' --mode local --port 8081",
        shell=True,
        capture_output=True,
        text=True
    )

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    with open("report_local.md", "a") as f:
        f.write(f"## 第{i}次执行:\n")
        f.write(f"- **开始时间**: {start_time.isoformat()}\n")
        f.write(f"- **结束时间**: {end_time.isoformat()}\n")
        f.write(f"- **耗时**: {duration:.2f}秒\n")
        f.write(f"- **输出**: {result.stdout.strip()}\n")
        f.write(f"- **错误**: {result.stderr.strip()}\n\n")

    time.sleep(1)
