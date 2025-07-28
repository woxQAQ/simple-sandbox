#!/usr/bin/env bash

# 启动代码沙箱服务
echo "Starting Code Sandbox..."

# 确保临时目录存在
mkdir -p /tmp/sandbox

# 启动FastAPI应用
exec uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 1