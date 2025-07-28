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