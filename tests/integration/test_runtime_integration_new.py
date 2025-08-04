"""
简化的运行时集成测试
使用新的测试环境
"""

import sys
from pathlib import Path

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# flake8: noqa: E402 - 需要先设置路径才能导入模块
from src.models import ExecutionStatus
from tests.utils.test_environment import (
    test_environment_context,
    test_runtime_manager,
)


class TestPythonRuntimeIntegration:
    """Python运行时集成测试"""

    def setup_method(self):
        """测试前设置"""
        self.runtime_manager = test_runtime_manager

    def test_simple_python_execution(self):
        """测试简单Python代码执行"""
        code = "print('Hello, World!')"

        with test_environment_context():
            python_runtime = self.runtime_manager.create_python_runtime()
            result = python_runtime.execute(code=code)

        assert result.status == ExecutionStatus.SUCCESS
        assert "Hello, World!" in result.stdout
        assert result.execution_time > 0

    def test_python_error_handling(self):
        """测试Python错误处理"""
        code = "1/0"

        with test_environment_context():
            python_runtime = self.runtime_manager.create_python_runtime()
            result = python_runtime.execute(code=code)

        assert result.status == ExecutionStatus.ERROR
        assert "division by zero" in result.stderr

    def test_python_timeout_handling(self):
        """测试Python超时处理"""
        code = "import time; time.sleep(100)"

        with test_environment_context():
            python_runtime = self.runtime_manager.create_python_runtime()
            result = python_runtime.execute(code=code)

        assert result.status == ExecutionStatus.TIMEOUT
        assert "超时" in result.stderr

    def test_python_input_handling(self):
        """测试Python输入处理"""
        code = "name = input(); print(f'Hello, {name}!')"
        input_data = "Alice"

        with test_environment_context():
            python_runtime = self.runtime_manager.create_python_runtime()
            result = python_runtime.execute(code=code, input_data=input_data)

        assert result.status == ExecutionStatus.SUCCESS
        assert "Hello, Alice!" in result.stdout


class TestNodeJSRuntimeIntegration:
    """Node.js运行时集成测试"""

    def setup_method(self):
        """测试前设置"""
        self.runtime_manager = test_runtime_manager

    def test_simple_nodejs_execution(self):
        """测试简单Node.js代码执行"""
        code = "console.log('Hello, Node.js!');"

        with test_environment_context():
            nodejs_runtime = self.runtime_manager.create_nodejs_runtime()
            result = nodejs_runtime.execute(code=code)

        assert result.status == ExecutionStatus.SUCCESS
        assert "Hello, Node.js!" in result.stdout
        assert result.execution_time > 0

    def test_nodejs_error_handling(self):
        """测试Node.js错误处理"""
        code = "console.log(undefinedVariable);"

        with test_environment_context():
            nodejs_runtime = self.runtime_manager.create_nodejs_runtime()
            result = nodejs_runtime.execute(code=code)

        assert result.status == ExecutionStatus.ERROR
        # 错误消息可能包含"ReferenceError"或"not defined"
        assert (
            "ReferenceError" in result.stderr or "not defined" in result.stderr
        )

    def test_nodejs_timeout_handling(self):
        """测试Node.js超时处理"""
        code = "while(true) {}"

        with test_environment_context():
            nodejs_runtime = self.runtime_manager.create_nodejs_runtime()
            result = nodejs_runtime.execute(code=code)

        assert result.status == ExecutionStatus.TIMEOUT
        assert "超时" in result.stderr


class TestConfigurationIntegration:
    """配置集成测试"""

    def test_test_environment_setup(self):
        """测试环境设置"""
        from tests.utils.test_environment import TestSandboxEnvironment

        sandbox = TestSandboxEnvironment()
        with sandbox.context():
            assert sandbox.config.test_mode is True

        # 清理后环境变量应该被移除
        import os

        assert "TEST_MODE" not in os.environ
        assert "DEBUG_MODE" not in os.environ


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
