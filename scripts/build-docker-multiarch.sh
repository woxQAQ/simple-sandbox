#!/usr/bin/env bash
set -e

# Docker Buildx 构建脚本
# 支持多平台构建：linux/amd64, linux/arm64

# 配置
IMAGE_NAME="${IMAGE_NAME:-woxqaq/code-sandbox}"
VERSION="${VERSION:-latest}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"
BUILDX_BUILDER="${BUILDX_BUILDER:-multi-platform}"

echo "🚀 Starting multi-platform Docker build..."
echo "📋 Configuration:"
echo "   Image: $IMAGE_NAME:$VERSION"
echo "   Platforms: $PLATFORMS"
echo "   Builder: $BUILDX_BUILDER"

# 检查docker buildx是否可用
if ! docker buildx inspect "$BUILDX_BUILDER" >/dev/null 2>&1; then
    echo "🔧 Creating buildx builder: $BUILDX_BUILDER"
    docker buildx create --name "$BUILDX_BUILDER" --use --driver docker-container --bootstrap
else
    echo "✅ Using existing buildx builder: $BUILDX_BUILDER"
    docker buildx use "$BUILDX_BUILDER"
fi

# 构建并推送
echo "🏗️  Building for platforms: $PLATFORMS"
docker buildx build \
    --platform "$PLATFORMS" \
    --tag "$IMAGE_NAME:$VERSION" \
    --tag "$IMAGE_NAME:latest" \
    --file docker/Dockerfile \
    --push \
    .

echo "🎉 Multi-platform build completed successfully!"
echo "📦 Available images:"
echo "   $IMAGE_NAME:$VERSION"
echo "   $IMAGE_NAME:latest"
echo "🏷️  Platforms: $PLATFORMS"