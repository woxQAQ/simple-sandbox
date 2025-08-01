"""
语言运行时集成测试
测试代码执行、结果收集、资源限制等功能
"""

from src.runtime.common.models import ExecutionStatus
from src.runtime.nodejs.runtime import NodeJSRuntime
from src.runtime.python.runtime import PythonRuntime


class TestPythonRuntimeIntegration:
    """Python运行时集成测试"""

    def setup_method(self):
        """测试前设置"""
        self.python_runtime = PythonRuntime()

    def test_simple_python_execution(self):
        """测试简单Python代码执行"""
        code = """
print("Hello, World!")
result = 2 + 2
print(f"Result: {result}")
"""
        result = self.python_runtime.execute(code=code)

        assert result.status == ExecutionStatus.SUCCESS
        assert result.exit_code == 0
        assert "Hello, World!" in result.stdout
        assert "Result: 4" in result.stdout
        assert result.execution_time > 0

    def test_python_error_handling(self):
        """测试Python错误处理"""
        code = """
# 故意制造错误
undefined_variable
"""
        result = self.python_runtime.execute(code=code)

        assert result.status == ExecutionStatus.ERROR
        assert result.exit_code != 0
        # 错误信息现在在error_message中
        assert (
            "NameError" in result.error_message
            or "undefined_variable" in result.error_message
        )

    def test_python_timeout_handling(self):
        """测试Python执行时间（无超时限制）"""
        code = """
import time
time.sleep(1)  # 短暂睡眠
print("This should be printed")
"""
        result = self.python_runtime.execute(code=code)

        # 现在没有超时限制，应该成功执行
        assert result.status == ExecutionStatus.SUCCESS
        assert "This should be printed" in result.stdout
        assert result.execution_time >= 1  # 至少睡了1秒  # 应该在超时前终止

    def test_python_input_handling(self):
        """测试Python输入处理"""
        code = """
import sys
data = sys.stdin.read().strip()
print(f"Input received: {data}")
"""
        input_data = "test input data"
        result = self.python_runtime.execute(code=code, input_data=input_data)

        assert result.status == ExecutionStatus.SUCCESS
        assert "Input received: test input data" in result.stdout

    def test_python_environment_variables(self):
        """测试Python环境变量处理（不再传递环境变量）"""
        code = """
import os
print(f"TEST_VAR: {os.environ.get('TEST_VAR', 'NOT_SET')}")
print(f"PYTHON_INPUT: {os.environ.get('PYTHON_INPUT', 'NOT_SET')}")
"""
        env_vars = {"TEST_VAR": "test_value"}
        input_data = "env_test"
        result = self.python_runtime.execute(
            code=code,
            input_data=input_data,
            env_vars=env_vars,
        )

        assert result.status == ExecutionStatus.SUCCESS
        # 环境变量不再传递到子进程，应该显示NOT_SET
        assert "TEST_VAR: NOT_SET" in result.stdout
        assert "PYTHON_INPUT: NOT_SET" in result.stdout

    def test_python_memory_limit(self):
        """测试Python内存处理（无限制）"""
        code = """
# 尝试分配大量内存
large_list = [0] * (100 * 1024 * 1024)  # 约100MB
print(f"List length: {len(large_list)}")
"""
        result = self.python_runtime.execute(code=code)

        # 现在没有内存限制，应该成功执行
        assert result.status == ExecutionStatus.SUCCESS
        assert "List length: 104857600" in result.stdout


class TestNodeJSRuntimeIntegration:
    """Node.js运行时集成测试"""

    def setup_method(self):
        """测试前设置"""
        self.nodejs_runtime = NodeJSRuntime()

    def test_simple_nodejs_execution(self):
        """测试简单Node.js代码执行"""
        code = """
console.log("Hello, Node.js!");
const result = 2 + 2;
console.log(`Result: ${result}`);
"""
        result = self.nodejs_runtime.execute(code=code)

        assert result.status == ExecutionStatus.SUCCESS
        assert result.exit_code == 0
        assert "Hello, Node.js!" in result.stdout
        assert "Result: 4" in result.stdout
        assert result.execution_time > 0

    def test_nodejs_error_handling(self):
        """测试Node.js错误处理"""
        code = """
// 故意制造错误
console.log(undefinedVariable);
"""
        result = self.nodejs_runtime.execute(code=code)

        assert result.status == ExecutionStatus.ERROR
        assert result.exit_code != 0
        # 错误信息可能在stderr或error_message中，且可能被console插件格式化
        error_content = result.stderr + (result.error_message or "")
        assert (
            "undefinedVariable" in error_content
            or "ReferenceError" in error_content
        )

    def test_nodejs_timeout_handling(self):
        """测试Node.js超时处理"""
        code = """
setTimeout(() => {
    console.log("This should be printed");
}, 1000);
"""
        result = self.nodejs_runtime.execute(code=code)

        # 应该成功执行（30秒超时限制）
        assert result.status == ExecutionStatus.SUCCESS
        assert "This should be printed" in result.stdout

    def test_nodejs_input_handling(self):
        """测试Node.js输入处理"""
        code = """
const input = require('fs').readFileSync(0, 'utf8');
console.log(`Input received: ${input.trim()}`);
"""
        input_data = "test input data"
        result = self.nodejs_runtime.execute(code=code, input_data=input_data)

        assert result.status == ExecutionStatus.SUCCESS
        assert "Input received: test input data" in result.stdout

    def test_nodejs_dangerous_modules_warning(self):
        """测试Node.js危险模块警告"""
        code = """
const fs = require('fs');
console.log("FS module loaded");
"""
        result = self.nodejs_runtime.execute(code=code)

        assert result.status == ExecutionStatus.SUCCESS
        assert "Warning: Module 'fs' is restricted" in result.stderr

    def test_nodejs_console_output_handling(self):
        """测试Node.js控制台输出处理"""
        code = """
console.log("Normal log");
console.error("Error log");
console.warn("Warning log");
"""
        result = self.nodejs_runtime.execute(code=code)

        assert result.status == ExecutionStatus.SUCCESS
        assert "Normal log" in result.stdout
        assert "Error log" in result.stderr
        assert "Warning log" in result.stderr


class TestRuntimeExtensions:
    """运行时扩展测试"""

    def test_python_runtime_extensions(self):
        """测试Python运行时扩展"""
        python_runtime = PythonRuntime()

        # 测试基本扩展功能
        code = """
# 测试扩展功能
print("Testing extensions")
"""
        result = python_runtime.execute(code=code)

        assert result.status == ExecutionStatus.SUCCESS
        assert "Testing extensions" in result.stdout

    def test_nodejs_runtime_extensions(self):
        """测试Node.js运行时扩展"""
        nodejs_runtime = NodeJSRuntime()

        # 测试预处理功能
        code = """
console.log("Testing preprocessing");
"""
        result = nodejs_runtime.execute(code=code)

        assert result.status == ExecutionStatus.SUCCESS
        assert "Testing preprocessing" in result.stdout
