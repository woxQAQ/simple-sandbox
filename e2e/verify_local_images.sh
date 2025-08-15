#!/bin/bash

# 验证本地镜像是否正常工作的脚本

echo "=== 验证本地镜像 ==="

# 检查镜像是否存在
echo "检查本地镜像..."
podman images | grep sandbox

echo ""
echo "=== 测试 Python 镜像 ==="
# 测试 Python 镜像
podman run --rm localhost/sandbox-python:latest python -c "print('Python 本地镜像工作正常!')"

echo ""
echo "=== 测试 Node.js 镜像 ==="
# 测试 Node.js 镜像
podman run --rm localhost/sandbox-node:latest node -e "console.log('Node.js 本地镜像工作正常!')"

echo ""
echo "=== 验证完成 ==="