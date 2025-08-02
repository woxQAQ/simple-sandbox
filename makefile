# 项目配置
IMAGE ?= woxqaq/code-sandbox
REGISTRY ?= docker.io
VERSION ?= latest
BUILDX_PLATFORM ?= linux/amd64,linux/arm64
BUILDX_ARGS ?= --sbom=false --provenance=false

# 主要目标
.PHONY: all fmt build test clean help

# 默认目标
all: fmt build test

# 代码格式化
fmt:
	@echo "🔧 Formatting code..."
	@ruff check . --fix
	@black .
	@isort .

# 构建安全组件
build-security:
	@echo "🔨 Building seccomp security components..."
	@./scripts/build.sh

# 清理构建产物
clean-security:
	@echo "🧹 Cleaning security build artifacts..."
	@./scripts/build.sh clean

# 完整构建
build: fmt build-security
	@echo "✅ Complete build finished"

# 完整清理
clean: clean-security
	@echo "✅ Complete cleanup finished"

# 测试相关目标
test-security:
	@echo "🔒 Testing security components..."
	@cd src/security/bpf && make test

# 运行所有测试
test: fmt build-security
	@echo "🧪 Running all tests..."
	@python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml

# 运行单元测试
test-unit:
	@echo "🔬 Running unit tests..."
	@python -m pytest tests/unit/ -v -m unit

# 运行集成测试
test-integration:
	@echo "🔌 Running integration tests..."
	@python -m pytest tests/integration/ -v -m integration

# 运行完整测试套件
test-all: fmt build-security
	@echo "🎯 Running complete test suite..."
	@python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml --cov-fail-under=60

# 运行代码质量检查
quality: fmt
	@echo "🛡️ Running code quality checks..."
	@bandit -r src/
	@echo "📦 Running safety check (may fail due to network issues)..."
	@-safety check || echo "⚠️  Safety check failed due to network issues - this is expected in some environments"

# ====================
# Docker 构建目标
# ====================

.PHONY: setup-builder clean-builder version build-image build-image-and-push build-multiarch build-test test-in-container run-container

# Docker Buildx 设置
setup-builder:
	@if ! docker buildx inspect multi-platform >/dev/null 2>&1; then \
		echo "🔧 Creating buildx builder: multi-platform"; \
		docker buildx create --name multi-platform --use --driver docker-container --bootstrap; \
	else \
		echo "✅ Using existing buildx builder: multi-platform"; \
		docker buildx use multi-platform; \
	fi

clean-builder:
	@if docker buildx inspect multi-platform >/dev/null 2>&1; then \
		echo "🧹 Removing buildx builder: multi-platform"; \
		docker buildx rm multi-platform; \
	fi

version:
	@echo "📦 Using version: $(VERSION)"

# 构建Docker镜像
build-image: setup-builder version
	@echo "🏗️ Building Docker image..."
	docker buildx build -t $(REGISTRY)/$(IMAGE):$(VERSION) \
		--platform $(BUILDX_PLATFORM) $(BUILDX_ARGS) \
	-f ./docker/Dockerfile .

# 使用镜像源构建Docker镜像
build-image-with-mirror: setup-builder version
	@echo "🏗️ Building Docker image with mirror acceleration..."
	docker buildx build -t $(REGISTRY)/$(IMAGE):$(VERSION) \
		--platform $(BUILDX_PLATFORM) $(BUILDX_ARGS) \
		--build-arg APT_MIRROR=mirrors.tuna.tsinghua.edu.cn \
		--build-arg PIP_MIRROR=https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple \
		--build-arg NPM_MIRROR=https://registry.npmmirror.com \
		-f ./docker/Dockerfile .

# 构建并推送Docker镜像
build-image-and-push: setup-builder version
	@echo "🚀 Building and pushing Docker image..."
	docker buildx build -t $(REGISTRY)/$(IMAGE):$(VERSION) \
		--platform $(BUILDX_PLATFORM) $(BUILDX_ARGS) --push \
	-f ./docker/Dockerfile .

# 多平台构建脚本
build-multiarch:
	@echo "🌍 Building multi-platform Docker image..."
	@./scripts/build-docker-multiarch.sh

# 本地测试构建
build-test:
	@echo "🧪 Building test image..."
	docker build -f ./docker/Dockerfile.test -t $(IMAGE):test .

# 在容器中运行测试
test-in-container: build-test
	@echo "🐳 Running tests in container..."
	docker run --rm $(IMAGE):test

# 交互式容器
run-container: build-test
	@echo "🌐 Starting interactive container..."
	docker run -it --rm -p 8000:8000 $(IMAGE):test

# ====================
# 帮助信息
# ====================

help:
	@echo "📖 Available targets:"
	@echo ""
	@echo "🔧 Development:"
	@echo "  all                           - Format, build, and test (default)"
	@echo "  fmt                           - Format code with ruff and black"
	@echo "  build                         - Complete build including security"
	@echo "  test                          - Run all tests"
	@echo "  clean                         - Complete cleanup"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test-unit                     - Run unit tests only"
	@echo "  test-integration              - Run integration tests only"
	@echo "  test-all                      - Run complete test suite with coverage"
	@echo "  test-security                 - Test security components"
	@echo "  quality                       - Run code quality checks"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  build-test                    - Build test image"
	@echo "  test-in-container             - Run tests in container"
	@echo "  run-container                 - Start interactive container"
	@echo "  build-image                   - Build Docker image"
	@echo "  build-image-with-mirror       - Build Docker image with mirror acceleration"
	@echo "  build-image-and-push          - Build and push Docker image"
	@echo "  build-multiarch               - Build multi-platform Docker image"
	@echo ""
	@echo "🛠️  Build System:"
	@echo "  build-security                - Build seccomp security components"
	@echo "  clean-security                - Clean security build artifacts"
	@echo "  setup-builder                 - Setup Docker buildx builder"
	@echo "  clean-builder                 - Clean Docker buildx builder"
	@echo ""
	@echo "📋 Help:"
	@echo "  help                          - Show this help message"
	@echo "  version                       - Show current version"
