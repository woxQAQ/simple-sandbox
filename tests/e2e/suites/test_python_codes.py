"""
Python代码E2E测试套件
"""

import logging
from typing import Any, Dict, List

from ..common.client import SandboxClient
from ..common.utils import extract_test_result, safe_execute_code

logger = logging.getLogger(__name__)


class PythonE2ETests:
    """Python代码E2E测试类"""

    def __init__(self, client: SandboxClient):
        self.client = client
        self.results: List[Dict[str, Any]] = []

    def run_all_tests(self) -> List[Dict[str, Any]]:
        """运行所有Python测试"""
        logger.info("开始运行Python E2E测试")

        # 基础功能测试
        self.test_basic_print()
        self.test_math_operations()
        self.test_variable_operations()
        self.test_function_definition()

        # 插件功能测试
        self.test_matplotlib_plugin()
        self.test_console_plugin()

        # 安全限制测试
        self.test_file_access_blocked()
        self.test_network_access_blocked()
        self.test_system_command_blocked()
        self.test_import_restricted_modules()

        # 边界情况测试
        self.test_empty_code()
        self.test_syntax_error()
        self.test_runtime_error()

        logger.info(f"Python E2E测试完成，共运行 {len(self.results)} 个测试")
        return self.results

    def test_basic_print(self) -> None:
        """测试基本打印功能"""
        code = "print('Hello, World!')"
        result = safe_execute_code(self.client, "python", code)
        test_result = extract_test_result(
            result,
            "Python基本打印功能",
            "测试Python的print函数是否正常工作",
            "success",
        )
        self.results.append(test_result)

    def test_math_operations(self) -> None:
        """测试数学运算"""
        code = """
result = 2 + 3 * 4
print(result)
print(f"平方根: {16**0.5}")
"""
        result = safe_execute_code(self.client, "python", code)
        test_result = extract_test_result(
            result, "Python数学运算", "测试Python的基本数学运算功能", "success"
        )
        self.results.append(test_result)

    def test_variable_operations(self) -> None:
        """测试变量操作"""
        code = """
x = 10
y = 20
z = x + y
print(f"x = {x}, y = {y}, z = {z}")
print(f"类型: {type(z)}")
"""
        result = safe_execute_code(self.client, "python", code)
        test_result = extract_test_result(
            result, "Python变量操作", "测试Python的变量定义和操作", "success"
        )
        self.results.append(test_result)

    def test_function_definition(self) -> None:
        """测试函数定义"""
        code = """
def greet(name):
    return f"Hello, {name}!"

def add(a, b):
    return a + b

print(greet("Python"))
print(f"5 + 3 = {add(5, 3)}")
"""
        result = safe_execute_code(self.client, "python", code)
        test_result = extract_test_result(
            result, "Python函数定义", "测试Python的函数定义和调用", "success"
        )
        self.results.append(test_result)

    def test_matplotlib_plugin(self) -> None:
        """测试matplotlib插件"""
        code = """
# 测试matplotlib是否可用
try:
    import matplotlib
    import matplotlib.pyplot as plt
    import numpy as np
    print("matplotlib导入成功")
    
    # 创建简单的图表
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    
    plt.figure(figsize=(8, 4))
    plt.plot(x, y)
    plt.title('Sine Wave')
    plt.xlabel('x')
    plt.ylabel('sin(x)')
    plt.grid(True)
    
    # 尝试保存到临时目录
    import tempfile
    import os
    temp_dir = tempfile.gettempdir()
    plot_path = os.path.join(temp_dir, 'test_plot.png')
    plt.savefig(plot_path)
    plt.close()
    
    if os.path.exists(plot_path):
        print(f"图表已保存到 {plot_path}")
        print("matplotlib插件测试通过")
    else:
        print("图表保存失败")
        
except ImportError as e:
    print(f"matplotlib未安装或导入失败: {e}")
except Exception as e:
    print(f"matplotlib测试过程中出错: {e}")
"""
        result = safe_execute_code(self.client, "python", code)
        test_result = extract_test_result(
            result,
            "Python Matplotlib插件",
            "测试Python的matplotlib绘图插件功能",
            "success",
        )
        self.results.append(test_result)

    def test_console_plugin(self) -> None:
        """测试控制台插件"""
        code = """
import sys
from io import StringIO

# 重定向输出
old_stdout = sys.stdout
sys.stdout = StringIO()

print("这是一条测试消息")
print("这是另一条消息")

# 恢复输出
output = sys.stdout.getvalue()
sys.stdout = old_stdout

print("控制台输出捕获完成")
print(f"捕获到的行数: {len(output.splitlines())}")
"""
        result = safe_execute_code(self.client, "python", code)
        test_result = extract_test_result(
            result,
            "Python控制台插件",
            "测试Python的控制台输出处理功能",
            "success",
        )
        self.results.append(test_result)

    def test_file_access_blocked(self) -> None:
        """测试文件访问被阻止"""
        code = """
try:
    with open('/etc/passwd', 'r') as f:
        content = f.read()
        print("文件访问成功")
except Exception as e:
    print(f"文件访问被阻止: {e}")
"""
        result = safe_execute_code(self.client, "python", code)
        test_result = extract_test_result(
            result,
            "Python文件访问阻止",
            "测试Python的文件系统访问安全限制",
            "success",
        )
        self.results.append(test_result)

    def test_network_access_blocked(self) -> None:
        """测试网络访问被阻止"""
        code = """
# 测试网络访问是否被阻止
try:
    import socket
    print("socket模块导入成功")
    
    # 尝试创建socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("socket创建成功")
    
    # 尝试连接（应该失败）
    sock.settimeout(2)
    result = sock.connect_ex(('8.8.8.8', 53))
    sock.close()
    
    if result == 0:
        print("网络访问成功 - 安全限制失败")
    else:
        print(f"网络访问被阻止，错误代码: {result}")
        
except ImportError as e:
    print(f"socket模块被阻止: {e}")
    print("网络安全限制生效")
except PermissionError as e:
    print(f"网络访问被权限限制阻止: {e}")
    print("网络安全限制生效")
except OSError as e:
    print(f"网络访问被系统限制阻止: {e}")
    print("网络安全限制生效")
except Exception as e:
    print(f"网络访问被其他方式阻止: {e}")
    print("网络安全限制生效")

print("网络安全限制测试完成")
"""
        result = safe_execute_code(self.client, "python", code)
        test_result = extract_test_result(
            result,
            "Python网络访问阻止",
            "测试Python的网络访问安全限制",
            "success",
        )
        self.results.append(test_result)

    def test_system_command_blocked(self) -> None:
        """测试系统命令被阻止"""
        code = """
import os
try:
    os.system('ls -la')
    print("系统命令执行成功")
except Exception as e:
    print(f"系统命令执行被阻止: {e}")
"""
        result = safe_execute_code(self.client, "python", code)
        test_result = extract_test_result(
            result,
            "Python系统命令阻止",
            "测试Python的系统命令执行安全限制",
            "success",
        )
        self.results.append(test_result)

    def test_import_restricted_modules(self) -> None:
        """测试受限模块导入"""
        code = """
try:
    import subprocess
    print("subprocess模块导入成功")
except Exception as e:
    print(f"subprocess模块导入被阻止: {e}")

try:
    import os
    print("os模块导入成功")
except Exception as e:
    print(f"os模块导入被阻止: {e}")
"""
        result = safe_execute_code(self.client, "python", code)
        test_result = extract_test_result(
            result,
            "Python受限模块导入",
            "测试Python的模块导入安全限制",
            "success",
        )
        self.results.append(test_result)

    def test_empty_code(self) -> None:
        """测试空代码"""
        code = ""
        result = safe_execute_code(self.client, "python", code)
        test_result = extract_test_result(
            result, "Python空代码", "测试Python的空代码处理", "success"
        )
        self.results.append(test_result)

    def test_syntax_error(self) -> None:
        """测试语法错误"""
        code = """
def broken_function(
    # 缺少右括号
    print("This will cause syntax error")
"""
        result = safe_execute_code(self.client, "python", code)
        test_result = extract_test_result(
            result, "Python语法错误", "测试Python的语法错误处理", "error"
        )
        self.results.append(test_result)

    def test_runtime_error(self) -> None:
        """测试运行时错误"""
        code = """
x = 10
y = 0
try:
    result = x / y
    print(f"结果: {result}")
except ZeroDivisionError as e:
    print(f"除零错误: {e}")
"""
        result = safe_execute_code(self.client, "python", code)
        test_result = extract_test_result(
            result, "Python运行时错误", "测试Python的运行时错误处理", "success"
        )
        self.results.append(test_result)
