FROM python:3.11-slim

# 创建非特权用户
RUN groupadd -r sandbox && useradd -r -g sandbox -u 1000 sandbox

# 安装系统依赖和Node.js
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY pyproject.toml ./

# 安装Python依赖
RUN pip install --no-cache-dir uv && \
    uv pip install --system -e .

# 安装Python常用包
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    matplotlib \
    pillow \
    scipy \
    requests \
    flask \
    django

# 创建必要的目录和设置权限
RUN mkdir -p /tmp/sandbox /app/logs && \
    chown -R sandbox:sandbox /tmp/sandbox /app/logs

# 复制应用代码
COPY src/ ./src/
COPY docker/entrypoint.sh ./docker/

# 设置文件权限
RUN chmod +x docker/entrypoint.sh && \
    chown -R sandbox:sandbox /app

# 使用非特权用户
USER sandbox

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# 暴露端口
EXPOSE 8000

# 启动命令
ENTRYPOINT ["./docker/entrypoint.sh"]