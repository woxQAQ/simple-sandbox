# e2e测试Makefile - 简化版
.PHONY: help install-deps run-tests clean test

# 默认目标
help:
	@echo "可用的命令："
	@echo "  install-deps    - 安装测试依赖"
	@echo "  run-tests       - 运行e2e测试"
	@echo "  clean           - 清理测试环境"
	@echo "  test            - 运行测试套件"

# 安装测试依赖
install-deps:
	@echo "安装测试依赖..."
	uv add docker pytest pytest-html requests python-dotenv --dev
	@echo "依赖安装完成"

# 运行e2e测试
run-tests:
	@echo "运行e2e测试..."
	python e2e-test.py

# 运行测试套件
test:
	@echo "运行测试套件..."
	pytest suites/ -v --html=reports/test_report.html --self-contained-html

# 清理测试环境
clean:
	@echo "清理测试环境..."
	docker stop sandbox-test || true
	docker rm sandbox-test || true
	docker rmi sandbox-test || true
	rm -rf reports/ __pycache__/ .pytest_cache/ *.log
	@echo "清理完成"