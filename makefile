.PHONY: fmt build-security test-security clean-security install-security docker-build docker-security docker-setup-buildx docker-build-multiarch docker-build-security-multiarch docker-push-multiarch docker-push-security-multiarch docker-push-all build-all clean-all help

# 代码格式化
fmt:
	@echo "Formatting code..."
	@ruff check . --fix
	@black .

# 构建安全组件
build-security:
	@echo "Building seccomp security components..."
	@./scripts/build.sh

# 测试安全组件
test-security:
	@echo "Testing security components..."
	@./scripts/build.sh test

# 清理构建产物
clean-security:
	@echo "Cleaning security build artifacts..."
	@./scripts/build.sh clean

# 安装到系统（仅Linux，需要sudo）
install-security: build-security
	@echo "Installing security components to system..."
	@cd src/security/bpf && make install

# 构建Docker镜像
docker-security:
	@echo "Building security Docker image..."
	@docker build -f docker/Dockerfile.security -t simple-sandbox-security .

# 构建主Docker镜像
docker-build:
	@echo "Building main Docker image..."
	@docker build -f docker/Dockerfile -t simple-sandbox .

# 设置Docker buildx（跨平台构建）
docker-setup-buildx:
	@echo "Setting up Docker buildx for cross-platform builds..."
	@docker buildx create --name multiarch --use --bootstrap || true
	@docker buildx inspect --bootstrap

# 跨平台构建主镜像（不推送）
docker-build-multiarch: docker-setup-buildx
	@echo "Building multi-architecture Docker image..."
	@docker buildx build \
		--platform linux/amd64,linux/arm64 \
		-f docker/Dockerfile \
		-t simple-sandbox:latest \
		--load .

# 跨平台构建安全镜像（不推送）
docker-build-security-multiarch: docker-setup-buildx
	@echo "Building multi-architecture security Docker image..."
	@docker buildx build \
		--platform linux/amd64,linux/arm64 \
		-f docker/Dockerfile.security \
		-t simple-sandbox-security:latest \
		--load .

# 跨平台构建并推送主镜像到Docker Hub
docker-push-multiarch: docker-setup-buildx
	@echo "Building and pushing multi-architecture Docker image..."
	@if [ -z "$(DOCKER_USERNAME)" ]; then \
		echo "Error: DOCKER_USERNAME environment variable is required"; \
		exit 1; \
	fi
	@docker buildx build \
		--platform linux/amd64,linux/arm64 \
		-f docker/Dockerfile \
		-t $(DOCKER_USERNAME)/simple-sandbox:latest \
		-t $(DOCKER_USERNAME)/simple-sandbox:$(shell git rev-parse --short HEAD) \
		--push .

# 跨平台构建并推送安全镜像到Docker Hub
docker-push-security-multiarch: docker-setup-buildx
	@echo "Building and pushing multi-architecture security Docker image..."
	@if [ -z "$(DOCKER_USERNAME)" ]; then \
		echo "Error: DOCKER_USERNAME environment variable is required"; \
		exit 1; \
	fi
	@docker buildx build \
		--platform linux/amd64,linux/arm64 \
		-f docker/Dockerfile.security \
		-t $(DOCKER_USERNAME)/simple-sandbox-security:latest \
		-t $(DOCKER_USERNAME)/simple-sandbox-security:$(shell git rev-parse --short HEAD) \
		--push .

# 推送所有镜像
docker-push-all: docker-push-multiarch docker-push-security-multiarch
	@echo "All Docker images pushed successfully"

# 完整构建（包括安全组件）
build-all: fmt build-security
	@echo "Complete build finished"

# 完整清理
clean-all: clean-security
	@echo "Complete cleanup finished"

# 帮助信息
help:
	@echo "Available targets:"
	@echo "  fmt                           - Format code with ruff and black"
	@echo "  build-security                - Build seccomp security components"
	@echo "  test-security                 - Test security components"
	@echo "  clean-security                - Clean security build artifacts"
	@echo "  install-security              - Install security components to system (Linux only)"
	@echo "  docker-build                  - Build main Docker image"
	@echo "  docker-security               - Build security Docker image"
	@echo "  docker-setup-buildx           - Setup Docker buildx for cross-platform builds"
	@echo "  docker-build-multiarch        - Build multi-architecture main image (local)"
	@echo "  docker-build-security-multiarch - Build multi-architecture security image (local)"
	@echo "  docker-push-multiarch         - Build and push multi-architecture main image to Docker Hub"
	@echo "  docker-push-security-multiarch - Build and push multi-architecture security image to Docker Hub"
	@echo "  docker-push-all               - Push all Docker images to Docker Hub"
	@echo "  build-all                     - Complete build including security"
	@echo "  clean-all                     - Complete cleanup"
	@echo "  help                          - Show this help message"
	@echo ""
	@echo "Docker Hub push targets require DOCKER_USERNAME environment variable:"
	@echo "  export DOCKER_USERNAME=your-dockerhub-username"
	@echo "  make docker-push-multiarch"