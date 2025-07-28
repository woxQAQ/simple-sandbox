#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

# 启动代码沙箱服务
echo "Starting Code Sandbox..."

# 启动FastAPI应用
exec uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 1