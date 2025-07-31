# E2E测试Makefile
# 管理e2e测试的构建、运行和清理

.PHONY: help test-local test-remote test-force build clean clean-all install-deps test-quick test-dev test-prod status

# 默认目标
help:
	@echo "E2E测试管理命令:"
	@echo "  test-local     - 使用本地构建的镜像运行测试"
	@echo "  test-remote    - 使用远程镜像运行测试"
	@echo "  test-force     - 强制重新构建本地镜像并运行测试"
	@echo "  test-quick     - 快速测试（使用现有镜像）"
	@echo "  test-dev       - 开发模式测试（本地构建，详细日志）"
	@echo "  test-prod      - 生产模式测试（远程镜像，简洁日志）"
	@echo "  build          - 构建本地测试镜像"
	@echo "  clean          - 清理测试容器和镜像"
	@echo "  clean-all      - 清理所有测试相关资源"
	@echo "  install-deps   - 安装测试依赖"
	@echo "  status         - 显示当前状态"
	@echo ""
	@echo "环境变量:"
	@echo "  USE_LOCAL_IMAGE - 是否使用本地镜像 (true/false)"
	@echo "  FORCE_BUILD     - 是否强制重新构建 (true/false)"
	@echo "  LOG_LEVEL       - 日志级别 (DEBUG/INFO/WARNING/ERROR)"

# 使用本地构建的镜像运行测试
test-local:
	@echo "使用本地构建的镜像运行e2e测试..."
	USE_LOCAL_IMAGE=true python e2e-test.py

# 使用远程镜像运行测试
test-remote:
	@echo "使用远程镜像运行e2e测试..."
	USE_LOCAL_IMAGE=false python e2e-test.py

# 强制重新构建本地镜像并运行测试
test-force:
	@echo "强制重新构建本地镜像并运行e2e测试..."
	USE_LOCAL_IMAGE=true FORCE_BUILD=true python e2e-test.py

# 快速测试（使用现有镜像）
test-quick:
	@echo "快速测试（使用现有镜像）..."
	USE_LOCAL_IMAGE=true FORCE_BUILD=false python e2e-test.py

# 开发模式测试（本地构建，详细日志）
test-dev:
	@echo "开发模式测试（本地构建，详细日志）..."
	LOG_LEVEL=DEBUG USE_LOCAL_IMAGE=true FORCE_BUILD=true python e2e-test.py

# 生产模式测试（远程镜像，简洁日志）
test-prod:
	@echo "生产模式测试（远程镜像，简洁日志）..."
	LOG_LEVEL=INFO USE_LOCAL_IMAGE=false FORCE_BUILD=false python e2e-test.py

# 构建本地测试镜像
build:
	@echo "构建本地测试镜像..."
	docker build -f ../../docker/Dockerfile.test -t sandbox-test ../..

# 安装测试依赖
install-deps:
	@echo "安装测试依赖..."
	uv add docker pytest pytest-html requests python-dotenv --dev
	@echo "依赖安装完成"

# 清理测试容器和镜像
clean:
	@echo "清理测试容器和镜像..."
	@# 停止并删除测试容器
	@docker ps -a --filter "name=sandbox-test" --format "{{.ID}}" | xargs -r docker stop
	@docker ps -a --filter "name=sandbox-test" --format "{{.ID}}" | xargs -r docker rm
	@# 删除本地测试镜像
	@docker images sandbox-test --format "{{.ID}}" | xargs -r docker rmi -f
	@echo "清理完成"

# 清理所有测试相关资源
clean-all: clean
	@echo "清理所有测试相关资源..."
	@# 删除日志文件
	@rm -f e2e_test.log
	@# 删除测试报告
	@rm -rf reports/
	@# 删除pytest缓存
	@rm -rf .pytest_cache/
	@# 删除Python缓存
	@rm -rf __pycache__/
	@echo "完全清理完成"

# 显示当前状态
status:
	@echo "=== 镜像状态 ==="
	@docker images | grep -E "(sandbox-test|woxqaq/simple-sandbox)" || echo "未找到相关镜像"
	@echo ""
	@echo "=== 容器状态 ==="
	@docker ps -a --filter "name=sandbox-test" || echo "未找到相关容器"
	@echo ""
	@echo "=== 文件状态 ==="
	@ls -la e2e_test.log 2>/dev/null || echo "无日志文件"
	@ls -la reports/ 2>/dev/null || echo "无报告目录"

# 兼容性命令（保持向后兼容）
run-tests: test-local
test: test-quick