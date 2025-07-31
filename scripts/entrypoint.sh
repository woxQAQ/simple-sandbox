#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

if [ "$TARGET_ARCH" = "amd64" ]; then
    NODEJS_ARCH="x64"
elif [ "$TARGET_ARCH" = "arm64" ]; then
    NODEJS_ARCH="arm64"
else
    echo "Unsupported architecture: $TARGET_ARCH"
    exit 1
fi

# 启动代码沙箱服务
echo "Starting Code Sandbox..."

# 解压Node.js
tar -xf /opt/node-${NODEJS_VERSION}-linux-${NODEJS_ARCH}.tar.xz -C /opt
echo "complete decompress the node"
ln -s /opt/node-${NODEJS_VERSION}-linux-${NODEJS_ARCH}.tar.xz/bin/node /usr/local/bin/node
rm -f /opt/node.tar.xz

echo "start sandbox server..."
# 启动简化HTTP服务器
exec python main.py --port 8000
