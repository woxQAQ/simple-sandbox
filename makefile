IMAGE ?= "woxqaq/simple-sandbox"
REGISTRY ?= "docker.io"
VERSION ?= "latest"
BUILDX_PLATFORM ?= "linux/amd64,linux/arm64"
BUILDX_ARGS ?= --sbom=false --provenance=false

.PHONY: fmt build-security test-security clean-security build clean-all help

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
	-f ./Dockerfile .

build-image-and-push: setup-builder version
	docker buildx build -t $(REGISTRY)/$(IMAGE):$(VERSION) \
		--platform $(BUILDX_PLATFORM) $(BUILDX_ARGS) --push \
	-f ./Dockerfile .

# 帮助信息
help:
	@echo "Available targets:"
	@echo "  fmt                           - Format code with ruff and black"
	@echo "  build-security                - Build seccomp security components"
	@echo "  test-security                 - Test security components"
	@echo "  clean-security                - Clean security build artifacts"
	@echo "  build                    	   - Complete build including security"
	@echo "  clean-all                     - Complete cleanup"
	@echo "  help                          - Show this help message"