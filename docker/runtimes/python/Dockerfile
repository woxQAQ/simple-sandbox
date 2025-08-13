FROM --platform=$BUILDPLATFORM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    MPLBACKEND=Agg \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安装系统依赖和设置用户环境（移除 apt 缓存挂载以避免锁文件冲突）
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends libfreetype6 libpng16-16 fonts-dejavu-core; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*; \
    useradd -m -u 65532 -s /usr/sbin/nologin sandbox; \
    mkdir -p /runner /workspace /tmp; \
    chown -R sandbox:sandbox /runner /workspace /tmp

# 先复制 requirements.txt 以利用 Docker 层缓存
COPY docker/runtimes/python/requirements.txt /tmp/requirements.txt

# 使用缓存挂载优化 pip 安装速度，修复语法错误
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# 复制应用代码
COPY docker/runtimes/python/runner.py /runner/runner.py

USER sandbox
WORKDIR /workspace

ENTRYPOINT ["python", "/runner/runner.py"]