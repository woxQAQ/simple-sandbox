#!/usr/bin/env bash

set -e

echo "Starting Code Sandbox..."

# 验证环境
echo "Python version: $(python --version)"
echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"

# 检查必要的目录
mkdir -p /var/sandbox/python /var/sandbox/nodejs

# 验证构建产物
if [ ! -f "/app/build/lib/libseccomp_injector_python.so" ]; then
    echo "Error: seccomp injector library not found"
    exit 1
fi

echo "Sandbox environment ready"
echo "Starting server..."

# 启动服务器
exec python main.py --port 8000
