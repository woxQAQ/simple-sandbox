"""
Python代码测试套件
测试Python代码执行、插件功能、安全限制等
"""

import logging

logger = logging.getLogger(__name__)


class TestPythonBasicExecution:
    """Python基本执行测试"""

    def test_hello_world(self, client):
        """测试Hello World"""
        code = 'print("Hello, World!")'
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "Hello, World!" in response.output
        assert response.execution_time is not None

    def test_variable_operations(self, client):
        """测试变量操作"""
        code = """
x = 10
y = 20
z = x + y
print(f"结果: {z}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "结果: 30" in response.output

    def test_function_definition(self, client):
        """测试函数定义"""
        code = """
def greet(name):
    return f"Hello, {name}!"

result = greet("Python")
print(result)
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "Hello, Python!" in response.output

    def test_list_operations(self, client):
        """测试列表操作"""
        code = """
numbers = [1, 2, 3, 4, 5]
numbers.append(6)
doubled = [x * 2 for x in numbers]
print(f"翻倍后的列表: {doubled}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "[2, 4, 6, 8, 10, 12]" in response.output


class TestPythonPlugins:
    """Python插件测试"""

    def test_console_plugin(self, client):
        """测试控制台插件"""
        code = """
import sys
from io import StringIO

# 测试标准输出
print("标准输出测试")

# 测试标准错误
print("错误输出测试", file=sys.stderr)

# 测试输入重定向（模拟）
print("输入输出测试完成")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "标准输出测试" in response.output

    def test_matplotlib_plugin(self, client):
        """测试matplotlib插件"""
        code = """
import matplotlib.pyplot as plt
import numpy as np

# 创建简单的图表
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 6))
plt.plot(x, y)
plt.title('正弦函数')
plt.xlabel('x')
plt.ylabel('sin(x)')
plt.grid(True)

print("matplotlib图表创建成功")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "matplotlib图表创建成功" in response.output

    def test_math_operations(self, client):
        """测试数学运算"""
        code = """
import math

# 测试各种数学函数
sqrt_result = math.sqrt(16)
pi_value = math.pi
sin_value = math.sin(math.pi/2)

print(f"平方根: {sqrt_result}")
print(f"π值: {pi_value}")
print(f"sin(π/2): {sin_value}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "平方根: 4.0" in response.output
        assert "sin(π/2): 1.0" in response.output


class TestPythonSecurity:
    """Python安全限制测试"""

    def test_file_operations_blocked(self, client):
        """测试文件操作被阻止"""
        code = """
# 尝试读取系统文件
try:
    with open('/etc/passwd', 'r') as f:
        content = f.read()
        print("文件读取成功")
except Exception as e:
    print(f"文件读取被阻止: {e}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert (
            "被阻止" in response.output
            or "Permission denied" in response.output
            or "文件读取被阻止" in response.output
            or "[SECURITY]" in response.output
        )

    def test_network_operations_blocked(self, client):
        """测试网络操作被阻止"""
        code = """
import socket

try:
    # 尝试创建socket连接
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('google.com', 80))
    print("网络连接成功")
    sock.close()
except Exception as e:
    print(f"网络操作被阻止: {e}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被阻止" in response.output

    def test_system_commands_blocked(self, client):
        """测试系统命令被阻止"""
        code = """
import os
import subprocess

try:
    # 尝试执行系统命令
    result = subprocess.run(['ls', '-la'], capture_output=True, text=True)
    print("命令执行成功")
    print(result.stdout)
except Exception as e:
    print(f"系统命令被阻止: {e}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被阻止" in response.output

    def test_import_dangerous_modules_blocked(self, client):
        """测试危险模块导入被阻止"""
        code = """
try:
    import os
    # 尝试执行危险操作
    os.system('echo "dangerous"')
    print("危险操作执行成功")
except Exception as e:
    print(f"危险操作被阻止: {e}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "被阻止" in response.output


class TestPythonAllowedOperations:
    """Python允许的操作测试"""

    def test_string_operations(self, client):
        """测试字符串操作"""
        code = """
text = "Hello, Python!"
upper_text = text.upper()
lower_text = text.lower()
reversed_text = text[::-1]

print(f"大写: {upper_text}")
print(f"小写: {lower_text}")
print(f"反转: {reversed_text}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "大写: HELLO, PYTHON!" in response.output

    def test_dict_operations(self, client):
        """测试字典操作"""
        code = """
person = {
    "name": "Alice",
    "age": 25,
    "city": "Beijing"
}

person["job"] = "Engineer"
age = person.get("age", 0)

print(f"姓名: {person['name']}")
print(f"年龄: {age}")
print(f"职业: {person['job']}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "姓名: Alice" in response.output
        assert "职业: Engineer" in response.output

    def test_exception_handling(self, client):
        """测试异常处理"""
        code = """
try:
    result = 10 / 0
except ZeroDivisionError:
    print("除零错误已捕获")
except Exception as e:
    print(f"其他错误: {e}")
finally:
    print("异常处理完成")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert "除零错误已捕获" in response.output
        assert "异常处理完成" in response.output

    def test_timeout_handling(self, client):
        """测试超时处理"""
        code = """
import time

# 测试长时间运行的操作
print("开始计时...")
time.sleep(2)
print("2秒后")
"""
        response = client.execute_python_code(code, timeout=5)

        assert response.success, f"执行失败: {response.error}"
        assert "开始计时..." in response.output
        assert "2秒后" in response.output


class TestPythonErrorHandling:
    """Python错误处理测试"""

    def test_syntax_error(self, client):
        """测试语法错误"""
        code = """
# 故意的语法错误
print("Hello"
"""
        response = client.execute_python_code(code)

        assert not response.success, "应该执行失败"
        assert (
            "SyntaxError" in response.error
            or "was never closed" in response.error
        )

    def test_runtime_error(self, client):
        """测试运行时错误"""
        code = """
# 故意的运行时错误
x = 10 / 0
"""
        response = client.execute_python_code(code)

        assert not response.success, "应该执行失败"
        assert (
            "ZeroDivisionError" in response.error
            or "division by zero" in response.error
        )

    def test_import_error(self, client):
        """测试导入错误"""
        code = """
# 尝试导入不存在的模块
import non_existent_module
"""
        response = client.execute_python_code(code)

        assert not response.success, "应该执行失败"
        assert (
            "ModuleNotFoundError" in response.error
            or "No module named" in response.error
        )

    def test_memory_error_handling(self, client):
        """测试内存错误处理"""
        code = """
# 测试内存限制
try:
    large_list = [0] * 1000000  # 1百万个元素
    print(f"创建了包含 {len(large_list)} 个元素的列表")
except MemoryError:
    print("内存不足")
except Exception as e:
    print(f"其他错误: {e}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert (
            "创建了包含" in response.output
            and "个元素的列表" in response.output
        )
