#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

# 启动代码沙箱服务
echo "Starting Code Sandbox..."

tar -xvf /opt/node.tar.xz -C /opt
ln -s /opt/node/bin/node /usr/local/bin/node
rm -f /opt/node.tar.xz

# 启动简化HTTP服务器
exec python main.py --port 8000
