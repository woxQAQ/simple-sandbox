IMAGE ?= "woxqaq/simple-sandbox"
REGISTRY ?= "docker.io"
VERSION ?= "latest"
BUILDX_PLATFORM ?= "linux/amd64,linux/arm64"
BUILDX_ARGS ?= --sbom=false --provenance=false

.PHONY: fmt build-security test-security clean-security build clean-all test test-unit test-integration test-all help

# 代码格式化
fmt:
	@echo "Formatting code..."
	@ruff check . --fix
	@black .
	@isort .

# 构建安全组件
build-security:
	@echo "Building seccomp security components..."
	@./scripts/build.sh

# 清理构建产物
clean-security:
	@echo "Cleaning security build artifacts..."
	@./scripts/build.sh clean

# 完整构建（包括安全组件）
build: fmt build-security
	@echo "Complete build finished"

# 完整清理
clean-all: clean-security
	@echo "Complete cleanup finished"

# 测试相关目标
test-security:
	@echo "Testing security components..."
	@cd src/security/bpf && make test

# 运行所有测试
test: fmt build-security
	@echo "Running all tests..."
	@python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml

# 运行单元测试
test-unit:
	@echo "Running unit tests..."
	@python -m pytest tests/unit/ -v -m unit

# 运行集成测试
test-integration:
	@echo "Running integration tests..."
	@python -m pytest tests/integration/ -v -m integration

# 运行完整测试套件
test-all: fmt build-security
	@echo "Running complete test suite..."
	@python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml --cov-fail-under=80

# 运行代码质量检查
quality: fmt
	@echo "Running code quality checks..."
	@bandit -r src/
	@safety check

########################
# 		build          #
########################

.PHONY: setup-builder clean-builder
setup-builder:
	@if ! docker buildx inspect multi-platform >/dev/null 2>&1; then \
		docker buildx create --name multi-platform --use --driver docker-container --bootstrap; \
	else \
		docker buildx use multi-platform; \
	fi

clean-builder:
	@if docker buildx inspect multi-platform >/dev/null 2>&1; then \
		docker buildx rm multi-platform; \
	fi

version:
	@echo "Using version: $(VERSION)"

build-image: setup-builder version
	docker buildx build -t $(REGISTRY)/$(IMAGE):$(VERSION) \
		--platform $(BUILDX_PLATFORM) $(BUILDX_ARGS) \
	-f ./docker/Dockerfile .

build-image-and-push: setup-builder version
	docker buildx build -t $(REGISTRY)/$(IMAGE):$(VERSION) \
		--platform $(BUILDX_PLATFORM) $(BUILDX_ARGS) --push \
	-f ./docker/Dockerfile .

# 帮助信息
help:
	@echo "Available targets:"
	@echo "  fmt                           - Format code with ruff and black"
	@echo "  build-security                - Build seccomp security components"
	@echo "  test-security                 - Test security components"
	@echo "  clean-security                - Clean security build artifacts"
	@echo "  build                    	   - Complete build including security"
	@echo "  clean-all                     - Complete cleanup"
	@echo "  test                          - Run all tests"
	@echo "  test-unit                     - Run unit tests only"
	@echo "  test-integration              - Run integration tests only"
	@echo "  test-all                      - Run complete test suite with coverage"
	@echo "  quality                       - Run code quality checks (bandit, safety)"
	@echo "  help                          - Show this help message"
