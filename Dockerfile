# Dockerfile for building seccomp security components
# Multi-stage build for Linux containers

# Build stage
FROM python:3.11-slim-bookworm AS builder
ARG DEBIAN_MIRROR="http://deb.debian.org/debian testing main"

# 安装构建依赖
RUN echo "deb ${DEBIAN_MIRROR}" > /etc/apt/sources.list \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    lib-seccomp \
    curl \
    wget \
    libc6-dev \
    linux-libc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY src /app
COPY scripts/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh
