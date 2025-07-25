from src.runtime import ExecutionStatus, PythonRuntime


class TestPythonRuntime:
    """测试Python运行时"""

    def setup_method(self):
        self.runtime = PythonRuntime()

    def test_simple_execution(self):
        """测试简单代码执行"""
        code = 'print("Hello, World!")'
        result = self.runtime.execute(code, timeout=5, memory_limit=64)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "Hello, World!" in result.stdout
        assert result.stderr == ""
        assert result.execution_time > 0

    def test_syntax_error(self):
        """测试语法错误处理"""
        code = 'print("Hello"  # 缺少右括号'
        result = self.runtime.execute(code, timeout=5, memory_limit=64)
        
        assert result.status == ExecutionStatus.ERROR
        assert "SyntaxError" in result.stderr or "syntax error" in result.stderr

    def test_timeout_handling(self):
        """测试超时处理"""
        code = '''
import time
time.sleep(10)
print("This should not print")
'''
        result = self.runtime.execute(code, timeout=1, memory_limit=64)
        
        assert result.status == ExecutionStatus.TIMEOUT

    def test_matplotlib_handling(self):
        """测试matplotlib处理"""
        code = '''
import matplotlib.pyplot as plt
import numpy as np

x = np.array([1, 2, 3, 4, 5])
y = x ** 2

plt.plot(x, y)
plt.show()
print("Plot generated")
'''
        result = self.runtime.execute(code, timeout=10, memory_limit=128)
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "Plot generated" in result.stdout
        # 检查是否包含base64图像数据
        assert "data:image/png;base64," in result.stdout

    def test_input_handling(self):
        """测试input函数处理"""
        code = '''
name = input("Enter your name: ")
print(f"Hello, {name}!")
'''
        input_data = "Alice"
        result = self.runtime.execute(
            code, timeout=5, memory_limit=64, input_data=input_data
        )
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "Hello, Alice!" in result.stdout

    def test_memory_limit(self):
        """测试内存限制"""
        code = '''
# 创建大列表来测试内存限制
big_list = [0] * 10000000
print("List created")
'''
        result = self.runtime.execute(code, timeout=5, memory_limit=32)
        
        # 32MB应该不足以容纳1000万个整数
        assert result.status in [ExecutionStatus.MEMORY_EXCEEDED, ExecutionStatus.ERROR]

    def test_environment_variables(self):
        """测试环境变量"""
        code = '''
import os
print(f"TEST_VAR: {os.getenv('TEST_VAR', 'not found')}")
'''
        env_vars = {"TEST_VAR": "test_value"}
        result = self.runtime.execute(
            code, timeout=5, memory_limit=64, env_vars=env_vars
        )
        
        assert result.status == ExecutionStatus.SUCCESS
        assert "TEST_VAR: test_value" in result.stdout

    def test_division_by_zero(self):
        """测试除零错误"""
        code = '''
result = 10 / 0
print("This won't print")
'''
        result = self.runtime.execute(code, timeout=5, memory_limit=64)
        
        assert result.status == ExecutionStatus.ERROR
        assert "ZeroDivisionError" in result.stderr

    def test_import_error(self):
        """测试导入错误"""
        code = '''
import nonexistent_module
print("This won't print")
'''
        result = self.runtime.execute(code, timeout=5, memory_limit=64)
        
        assert result.status == ExecutionStatus.ERROR
        assert "ModuleNotFoundError" in result.stderr or "ImportError" in result.stderr