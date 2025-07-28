# Dockerfile for building seccomp security components
# Multi-stage build for Linux containers

# Build stage
ARG DEBIAN_MIRROR="http://deb.debian.org/debian testing main"
ARG NODEJS_VERSION=v20.11.0
ARG TARGETARCH
FROM python:3.11.13-slim-bookworm AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./

# 安装构建依赖
RUN echo "deb ${DEBIAN_MIRROR}" > /etc/apt/sources.list \
    apt update && apt install -y --no-install-recommends \
    build-essential \
    curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && /root/.local/bin/uv venv /opt/venv --python 3.11 \
    && . /opt/venv/bin/activate \
    && /root/.local/bin/uv sync --active \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN ./build.sh

# Final Stage
FROM python:3.11.13-slim

RUN echo "deb ${DEBIAN_MIRROR}" > /etc/apt/sources.list \
    apt update && apt install -y --no-install-recommends \
    wget \
    curl \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN ./scripts/install_nodejs.sh ${NODEJS_VERSION} ${TARGETARCH}

# copy language runtime from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/build/lib /app/build/lib

ENV PATH="/opt/venv/bin:$PATH"

COPY . /app
WORKDIR /app

RUN . /opt/venv/bin/activate && pip install --no-deps -e . && \
    rm -rf /tmp/*

ENTRYPOINT [ "/app/scripts/entrypoint.sh" ]
