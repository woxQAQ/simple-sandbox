# Dockerfile for Code Sandbox
# Multi-architecture build using docker buildx

# Build stage - compile seccomp components and install dependencies
FROM --platform=$BUILDPLATFORM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libseccomp-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./
COPY scripts/ ./scripts/

# Install Python dependencies
RUN pip install -e .

# Copy source code
COPY src/ ./src/

# Build seccomp components
RUN chmod +x ./scripts/build.sh && ./scripts/build.sh

# Install Node.js transformer dependencies
RUN cd src/runtime/nodejs && npm install

# Final stage - runtime image
FROM --platform=$TARGETPLATFORM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libseccomp-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Node.js for runtime
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

WORKDIR /app

# Copy application files
COPY --from=builder /app/src ./src
COPY --from=builder /app/build ./build
COPY --from=builder /app/scripts ./scripts
COPY pyproject.toml ./
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/src/runtime/nodejs/node_modules ./src/runtime/nodejs/node_modules

# Create sandbox directories
RUN mkdir -p /var/sandbox/python /var/sandbox/nodejs

# Set environment variables
ENV PYTHONPATH=/app
ENV NODE_PATH=/app/src/runtime/nodejs
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd -m -u 1000 sandbox && \
    chown -R sandbox:sandbox /app /var/sandbox
USER sandbox

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Default command
CMD ["python", "main.py", "--port", "8000"]
