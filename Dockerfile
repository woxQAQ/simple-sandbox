# Dockerfile for building seccomp security components
# Multi-stage build for Linux containers

# Build stage
FROM python:3.11-slim-bookworm AS builder
ARG DEBIAN_MIRROR="http://deb.debian.org/debian testing main"

# 安装构建依赖
RUN echo "deb ${DEBIAN_MIRROR}" > /etc/apt/sources.list \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    lib-seccomp \
    curl \
    wget \
    libc6-dev \
    linux-libc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /build

# 复制源代码
COPY src/ ./src/
COPY ./build.sh ./
COPY build/ ./build/

# 构建安全组件
RUN ./build_security.sh

# 运行时阶段
FROM ubuntu:22.04 AS runtime

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 创建非特权用户
RUN groupadd -r sandbox && useradd -r -g sandbox sandbox

# 设置工作目录
WORKDIR /app

# 从构建阶段复制构建产物
COPY --from=builder /build/build/lib/ /usr/local/lib/
COPY --from=builder /build/src/security/ ./src/security/
COPY --from=builder /build/build/seccomp/ ./build/seccomp/

# 更新动态链接器缓存
RUN ldconfig

# 设置Python路径
ENV PYTHONPATH=/app

# 验证安装
RUN python3 -c "from src.security import SecurityManager; print('Security components loaded successfully')"

# 默认命令
CMD ["python3", "-c", "from src.security import SecurityManager; sm = SecurityManager(); print(f'Seccomp supported: {sm.is_seccomp_supported()}')"]