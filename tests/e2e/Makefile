# E2E测试 Makefile
# 提供E2E测试的快捷命令

.PHONY: help run-e2e clean-deps install-deps build-image serve-allure

# 默认目标
help:
	@echo "E2E测试可用命令:"
	@echo "  run-e2e     - 运行完整的E2E测试"
	@echo "  install-deps - 安装E2E测试依赖"
	@echo "  clean-deps  - 清理依赖文件"
	@echo "  build-image - 构建Docker镜像"
	@echo "  serve-allure - 启动Allure报告服务"

# 运行E2E测试
run-e2e:
	@echo "开始运行E2E测试..."
	uv run e2e.py

# 安装E2E测试依赖
install-deps:
	@echo "安装E2E测试依赖..."
	uv add pydantic-settings --dev
	uv add requests --dev
	uv add docker --dev
	uv add pytest --dev
	uv add allure-pytest --dev
	@echo "安装Allure命令行工具..."
	@if command -v allure >/dev/null 2>&1; then \
		echo "Allure已安装"; \
	else \
		echo "请手动安装Allure: https://docs.qameta.io/allure/#_installing_a_commandline"; \
	fi

# 清理依赖
clean-deps:
	@echo "清理依赖文件..."
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -f coverage.xml
	rm -f e2e_test.log

# 构建Docker镜像
build-image:
	@echo "构建Docker镜像..."
	docker build -t code-sandbox:latest -f docker/Dockerfile .

# 启动Allure报告服务
serve-allure:
	@echo "启动Allure报告服务..."
	@if [ ! -d "reports/allure-results" ]; then \
		echo "错误: 未找到allure-results目录，请先运行E2E测试"; \
		exit 1; \
	fi
	allure serve reports/allure-results
