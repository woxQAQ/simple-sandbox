#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

# 启动代码沙箱服务
echo "Starting Code Sandbox..."

# 启动简化HTTP服务器
exec python main.py --port 8000
