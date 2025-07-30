#!/usr/bin/env bash
NODEJS_VERSION=$1
TARGETARCH=$2
NODEJS_MIRROR="https://nodejs.org/dist"

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
tar -xf /opt/node/node-${NODEJS_VERSION}-${NODEJS_ARCH}.tar.xz -C /opt/node --strip-components=1
rm /opt/node/node-${NODEJS_VERSION}-${NODEJS_ARCH}.tar.xz
