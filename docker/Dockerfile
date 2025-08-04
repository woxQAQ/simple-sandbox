# Dockerfile for Code Sandbox
# Multi-architecture build using docker buildx

# Build stage - compile seccomp components and install dependencies
FROM --platform=$BUILDPLATFORM python:3.11-slim AS builder

# Configure APT mirror if provided
ARG APT_MIRROR=""
RUN if [ -n "$APT_MIRROR" ]; then \
    echo "Using APT mirror: $APT_MIRROR"; \
    sed -i "s|deb.debian.org|$APT_MIRROR|g" /etc/apt/sources.list; \
    fi

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libseccomp-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Configure Node.js mirror if provided
ARG NPM_MIRROR=""
RUN if [ -n "$NPM_MIRROR" ]; then \
    echo "Using NPM mirror: $NPM_MIRROR"; \
    npm config set registry "$NPM_MIRROR"; \
    fi

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./
COPY scripts/ ./scripts/

# Configure pip mirror if provided
ARG PIP_MIRROR=""
RUN if [ -n "$PIP_MIRROR" ]; then \
    echo "Using pip mirror: $PIP_MIRROR"; \
    pip config set global.index-url "$PIP_MIRROR"; \
    fi

# Install Python dependencies
RUN pip install -e .

# Copy source code
COPY src/ ./src/
COPY main.py ./

# Build seccomp components
RUN chmod +x ./scripts/build.sh && ./scripts/build.sh

RUN cd src/runtime/nodejs/node_runtime && npm install

# Final stage - runtime image
FROM --platform=$TARGETPLATFORM python:3.11-slim

# Configure APT mirror if provided
ARG APT_MIRROR=""
RUN if [ -n "$APT_MIRROR" ]; then \
    echo "Using APT mirror: $APT_MIRROR"; \
    sed -i "s|deb.debian.org|$APT_MIRROR|g" /etc/apt/sources.list; \
    fi

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libseccomp-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Configure Node.js mirror if provided
ARG NPM_MIRROR=""
RUN if [ -n "$NPM_MIRROR" ]; then \
    echo "Using NPM mirror: $NPM_MIRROR"; \
    npm config set registry "$NPM_MIRROR"; \
    fi

# Install Node.js for runtime
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

WORKDIR /app

# Copy application files
COPY --from=builder /app/src ./src
COPY --from=builder /app/build ./build
COPY --from=builder /app/scripts ./scripts
COPY --from=builder /app/main.py ./main.py
COPY pyproject.toml ./
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# Node.js transformer dependencies removed

# Copy seccomp libraries to language-specific directories
RUN mkdir -p /var/sandbox/python /var/sandbox/nodejs/runtime/ && \
    cp /app/build/lib/libseccomp_injector_python.so /var/sandbox/python/ && \
    cp /app/build/lib/libseccomp_injector_nodejs.so /var/sandbox/nodejs/

COPY /app/src/runtime/nodejs/node_runtime /var/sandbox/nodejs/runtime

# Set environment variables
ENV PYTHONPATH=/app
ENV NODE_PATH=/app/src/runtime/nodejs
ENV PYTHONUNBUFFERED=1

# Create non-root user for security (but don't switch to it)
RUN useradd -m -u 1000 sandbox && \
    chown -R sandbox:sandbox /app /var/sandbox

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Keep root user for chroot functionality
# Language runtime processes will drop privileges to sandbox user

# Default command
CMD ["python", "main.py", "--port", "8000"]
