# Dockerfile for building seccomp security components
# Multi-stage build for Linux containers

# Build stage
FROM python:3.11.13-slim-bookworm AS builder
ARG DEBIAN_MIRROR="http://deb.debian.org/debian testing main"
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY scripts/ ./scripts/
COPY src/ ./src/

# 安装构建依赖
RUN echo "deb ${DEBIAN_MIRROR}" > /etc/apt/sources.list && \
    apt update && apt install -y --no-install-recommends \
    build-essential \
    curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && /root/.local/bin/uv venv /opt/venv --python 3.11 \
    && . /opt/venv/bin/activate \
    && /root/.local/bin/uv sync --active \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN ./scripts/build.sh

# build transformer package
FROM node:20.11.0-alpine as node_builder

COPY src/ ./src/
RUN cd src/runtime/transformer/nodejs && npm install

# Final Stage
FROM python:3.11.13-slim

# 重新声明ARG变量
ARG DEBIAN_MIRROR="http://deb.debian.org/debian testing main"
ARG NODEJS_VERSION=v20.11.0
ARG TARGETARCH

RUN echo "deb ${DEBIAN_MIRROR}" > /etc/apt/sources.list && \
    apt update && apt install -y --no-install-recommends \
    wget \
    curl \
    xz-utils \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY . /app

RUN /app/scripts/install_nodejs.sh ${NODEJS_VERSION} ${TARGETARCH}
# copy language runtime from builder
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:/opt/node/bin:$PATH"

COPY --from=builder /app/build/lib /app/build/lib
COPY --from=node_builder /src/runtime/transformer/nodejs/node_modules /app/src/runtime/transformer/nodejs/node_modules
WORKDIR /app

RUN . /opt/venv/bin/activate && pip install --no-deps -e . && \
    rm -rf /tmp/*

ENTRYPOINT [ "/app/scripts/entrypoint.sh" ]
