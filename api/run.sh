#!/bin/bash
# 家电状态 API 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ">>> 安装依赖..."
pip install -r requirements.txt -q

echo ">>> 启动 API 服务 (端口 8090)..."
python appliance_api.py
