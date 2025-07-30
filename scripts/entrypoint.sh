#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

# 启动代码沙箱服务
echo "Starting Code Sandbox..."

# 解压并设置Node.js（如果尚未设置）
if [ ! -d "/opt/node/nodejs" ]; then
    echo "Setting up Node.js..."
    cd /opt/node
    # 查找tar.xz文件
    NODEJS_TAR=$(ls node-*.tar.xz | head -1)
    if [ -n "$NODEJS_TAR" ]; then
        tar -xf "$NODEJS_TAR"
        NODEJS_DIR=$(echo "$NODEJS_TAR" | sed 's/\.tar\.xz$//')
        mv "$NODEJS_DIR" nodejs
        rm "$NODEJS_TAR"

        # 添加Node.js到PATH
        ln -sf /opt/node/nodejs/bin/node /usr/local/bin/node
        ln -sf /opt/node/nodejs/bin/npm /usr/local/bin/npm
        cd /app/src/runtime/transformer/nodejs && npm install

        echo "Node.js setup completed:"
        /opt/node/nodejs/bin/node --version
    else
        echo "Error: Node.js tarball not found"
        exit 1
    fi
fi

# 启动简化HTTP服务器
exec python main.py --port 8000
