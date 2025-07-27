.PHONY: fmt build-security test-security clean-security install-security docker-security help

# 代码格式化
fmt:
	@echo "Formatting code..."
	@ruff check . --fix
	@black .

# 构建安全组件
build-security:
	@echo "Building seccomp security components..."
	@./build_security.sh

# 测试安全组件
test-security:
	@echo "Testing security components..."
	@./build_security.sh test

# 清理构建产物
clean-security:
	@echo "Cleaning security build artifacts..."
	@./build_security.sh clean

# 安装到系统（仅Linux，需要sudo）
install-security: build-security
	@echo "Installing security components to system..."
	@cd src/security/bpf && make install

# 构建Docker镜像
docker-security:
	@echo "Building security Docker image..."
	@docker build -f Dockerfile.security -t simple-sandbox-security .

# 完整构建（包括安全组件）
build-all: fmt build-security
	@echo "Complete build finished"

# 完整清理
clean-all: clean-security
	@echo "Complete cleanup finished"

# 帮助信息
help:
	@echo "Available targets:"
	@echo "  fmt              - Format code with ruff and black"
	@echo "  build-security   - Build seccomp security components"
	@echo "  test-security    - Test security components"
	@echo "  clean-security   - Clean security build artifacts"
	@echo "  install-security - Install security components to system (Linux only)"
	@echo "  docker-security  - Build security Docker image"
	@echo "  build-all        - Complete build including security"
	@echo "  clean-all        - Complete cleanup"
	@echo "  help             - Show this help message"