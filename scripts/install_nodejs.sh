#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

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

mkdir -p /opt
wget -O /opt/node.tar.xz \
       ${NODEJS_MIRROR}/${NODEJS_VERSION}/node-${NODEJS_VERSION}-linux-${NODEJS_ARCH}.tar.xz
