#!/usr/bin/env bash
NODEJS_VERSION=$1
TARGETARCH=$2
NODEJS_MIRROR="https://registry.npmmirror.com/mirrors/node"

if [ "$TARGETARCH" = "amd64" ]; then
    NODEJS_ARCH="x64"
elif [ "$TARGETARCH" = "arm64" ]; then
    NODEJS_ARCH="arm64"
else
    echo "Unsupported architecture: $TARGETARCH"
    exit 1
fi

mkdir -p /opt/node
wget -O /opt/node/node-${NODEJS_VERSION}-${NODEJS_ARCH}.tar.xz \
       ${NODEJS_MIRROR}/${NODEJS_VERSION}/node-${NODEJS_VERSION}-${NODEJS_ARCH}.tar.xz

cd /opt/node
tar -xJf node-${NODEJS_VERSION}-${NODEJS_ARCH}.tar.xz

NODEJS_DIR="node-${NODEJS_VERSION}-${NODEJS_ARCH}"
mv "$NODEJS_DIR" nodejs
rm node-${NODEJS_VERSION}-${NODEJS_ARCH}.tar.xz

# 添加Node.js到PATH
ln -sf /opt/node/nodejs/bin/node /usr/local/bin/node
ln -sf /opt/node/nodejs/bin/npm /usr/local/bin/npm

# 安装Node.js transformer依赖
if [ -d "/app/src/runtime/transformer/nodejs" ]; then
    cd /app/src/runtime/transformer/nodejs && npm install
else
    echo "Warning: Node.js transformer directory not found, skipping npm install"
fi

echo "Node.js setup completed:"
/opt/node/nodejs/bin/node --version
