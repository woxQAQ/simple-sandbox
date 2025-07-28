.PHONY: fmt build-security test-security clean-security build clean-all help

# 代码格式化
fmt:
	@echo "Formatting code..."
	@ruff check . --fix
	@black .

# 构建安全组件
build-security:
	@echo "Building seccomp security components..."
	@./scripts/build.sh

# 测试相关命令
.PHONY: test test-unit test-integration test-e2e test-security test-performance test-quick test-smoke test-all test-coverage test-lint test-security-scan

# 运行所有测试
test:
	uv run python scripts/run_tests.py all

# 单元测试
test-unit:
	uv run python scripts/run_tests.py unit

# 集成测试
test-integration:
	uv run python scripts/run_tests.py integration

# 端到端测试
test-e2e:
	uv run python scripts/run_tests.py e2e

# 安全测试
test-security:
	uv run python scripts/run_tests.py security

# 性能测试
test-performance:
	uv run python scripts/run_tests.py performance

# 快速测试（单元 + 基本集成）
test-quick:
	uv run python scripts/run_tests.py quick

# 冒烟测试
test-smoke:
	uv run python scripts/run_tests.py smoke

# 运行所有测试（包括慢速测试）
test-all:
	uv run python scripts/run_tests.py all --include-slow

# 生成覆盖率报告
test-coverage:
	uv run python scripts/run_tests.py coverage

# 代码检查
test-lint:
	uv run python scripts/run_tests.py lint

# 安全扫描
test-security-scan:
	uv run python scripts/run_tests.py security-scan

# 清理测试产物
test-clean:
	uv run python scripts/run_tests.py clean

# 详细测试（带详细输出）
test-verbose:
	uv run python scripts/run_tests.py all -v

# 运行特定测试文件
test-file:
	@echo "Usage: make test-file FILE=tests/unit/api/test_models.py"
	@if [ -z "$(FILE)" ]; then echo "Error: FILE parameter is required"; exit 1; fi
	uv run python scripts/run_tests.py specific $(FILE)

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