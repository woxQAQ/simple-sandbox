#!/usr/bin/env bash
set -e

echo "Building seccomp security components..."

# 创建构建目录
mkdir -p build/lib build/logs

# 构建共享库
echo "Building seccomp injector shared library..."
cd src/security/bpf

# 清理之前的构建
make clean 2>/dev/null || true

# 构建
if make all 2>&1 | tee ../../../build/logs/build.log; then
    echo "✅ Shared library built successfully"
else
    echo "❌ Failed to build shared library"
    cd ../../..
    exit 1
fi

cd ../../..

echo "🎉 Build completed successfully!"
echo "📁 Shared library location: build/lib/"
echo "📋 Build logs: build/logs/"
