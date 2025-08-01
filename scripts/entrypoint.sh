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

NODE_TAR_NAME=node-${NODEJS_VERSION}-linux-${NODEJS_ARCH}

# 解压Node.js
tar -xf /opt/${NODE_TAR_NAME}.tar.xz -C /opt
echo "complete decompress the node"
ln -s /opt/${NODE_TAR_NAME}/bin/node /usr/local/bin/node
rm -f /opt/${NODE_TAR_NAME}.tar.xz

echo "create sandbox user"
sh /app/scripts/create_sandbox_user.sh

if [ -z "${SANDBOX_GROUP_ID}" ]; then
    echo "env variable ${SANDBOX_GROUP_ID} has not been set"

if [ -z "${SANDBOX_USER_ID}" ]; then
    echo "env variable ${SANDBOX_GROUP_ID} has not been set"

echo "start sandbox server..."
# 启动简化HTTP服务器
exec python main.py --port 8000
