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
    """Python安全限制测试 - 基于seccomp系统调用过滤"""

    def test_ptrace_blocked(self, client):
        """测试ptrace系统调用被阻止"""
        code = """
import ctypes
import os
import errno

# 尝试使用ptrace系统调用
libc = ctypes.CDLL(None)
ptrace = libc.ptrace
ptrace.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
ptrace.restype = ctypes.c_long

try:
    # PTRACE_TRACEME = 0
    result = ptrace(0, 0, None, None)
    if result == -1:
        error = ctypes.get_errno()
        if error == errno.EPERM:
            print("ptrace被seccomp规则阻止: Operation not permitted")
        else:
            print(f"ptrace失败，错误码: {error}")
    else:
        print("ptrace调用成功")
except Exception as e:
    print(f"ptrace调用异常: {e}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert (
            "被seccomp规则阻止" in response.output
            or "Operation not permitted" in response.output
        )

    def test_chmod_blocked(self, client):
        """测试chmod系统调用被阻止"""
        code = """
import ctypes
import os
import errno

# 尝试使用chmod系统调用
libc = ctypes.CDLL(None)
chmod = libc.chmod
chmod.argtypes = [ctypes.c_char_p, ctypes.c_uint]
chmod.restype = ctypes.c_int

try:
    # 尝试修改文件权限
    result = chmod(b"/tmp/test.txt", 0o777)
    if result == -1:
        error = ctypes.get_errno()
        if error == errno.EPERM:
            print("chmod被seccomp规则阻止: Operation not permitted")
        else:
            print(f"chmod失败，错误码: {error}")
    else:
        print("chmod调用成功")
except Exception as e:
    print(f"chmod调用异常: {e}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert (
            "被seccomp规则阻止" in response.output
            or "Operation not permitted" in response.output
        )

    def test_mkdir_blocked(self, client):
        """测试mkdir系统调用被阻止"""
        code = """
import ctypes
import errno

# 尝试使用mkdir系统调用
libc = ctypes.CDLL(None)
mkdir = libc.mkdir
mkdir.argtypes = [ctypes.c_char_p, ctypes.c_uint]
mkdir.restype = ctypes.c_int

try:
    # 尝试创建目录
    result = mkdir(b"/tmp/test_dir", 0o755)
    if result == -1:
        error = ctypes.get_errno()
        if error == errno.EPERM:
            print("mkdir被seccomp规则阻止: Operation not permitted")
        else:
            print(f"mkdir失败，错误码: {error}")
    else:
        print("mkdir调用成功")
except Exception as e:
    print(f"mkdir调用异常: {e}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert (
            "被seccomp规则阻止" in response.output
            or "Operation not permitted" in response.output
        )

    def test_unlink_blocked(self, client):
        """测试unlink系统调用被阻止"""
        code = """
import ctypes
import errno

# 尝试使用unlink系统调用
libc = ctypes.CDLL(None)
unlink = libc.unlink
unlink.argtypes = [ctypes.c_char_p]
unlink.restype = ctypes.c_int

try:
    # 尝试删除文件
    result = unlink(b"/tmp/nonexistent.txt")
    if result == -1:
        error = ctypes.get_errno()
        if error == errno.EPERM:
            print("unlink被seccomp规则阻止: Operation not permitted")
        else:
            print(f"unlink失败，错误码: {error}")
    else:
        print("unlink调用成功")
except Exception as e:
    print(f"unlink调用异常: {e}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert (
            "被seccomp规则阻止" in response.output
            or "Operation not permitted" in response.output
        )

    def test_rename_blocked(self, client):
        """测试rename系统调用被阻止"""
        code = """
import ctypes
import errno

# 尝试使用rename系统调用
libc = ctypes.CDLL(None)
rename = libc.rename
rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
rename.restype = ctypes.c_int

try:
    # 尝试重命名文件
    result = rename(b"/tmp/nonexistent1.txt", b"/tmp/nonexistent2.txt")
    if result == -1:
        error = ctypes.get_errno()
        if error == errno.EPERM:
            print("rename被seccomp规则阻止: Operation not permitted")
        else:
            print(f"rename失败，错误码: {error}")
    else:
        print("rename调用成功")
except Exception as e:
    print(f"rename调用异常: {e}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert (
            "被seccomp规则阻止" in response.output
            or "Operation not permitted" in response.output
        )

    def test_rmdir_blocked(self, client):
        """测试rmdir系统调用被阻止"""
        code = """
import ctypes
import errno

# 尝试使用rmdir系统调用
libc = ctypes.CDLL(None)
rmdir = libc.rmdir
rmdir.argtypes = [ctypes.c_char_p]
rmdir.restype = ctypes.c_int

try:
    # 尝试删除目录
    result = rmdir(b"/tmp/nonexistent_dir")
    if result == -1:
        error = ctypes.get_errno()
        if error == errno.EPERM:
            print("rmdir被seccomp规则阻止: Operation not permitted")
        else:
            print(f"rmdir失败，错误码: {error}")
    else:
        print("rmdir调用成功")
except Exception as e:
    print(f"rmdir调用异常: {e}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert (
            "被seccomp规则阻止" in response.output
            or "Operation not permitted" in response.output
        )

    def test_mount_blocked(self, client):
        """测试mount系统调用被阻止"""
        code = """
import ctypes
import errno

# 尝试使用mount系统调用
libc = ctypes.CDLL(None)
mount = libc.mount
mount.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_void_p]
mount.restype = ctypes.c_int

try:
    # 尝试挂载proc文件系统
    result = mount(b"proc", b"/tmp", b"proc", 0, None)
    if result == -1:
        error = ctypes.get_errno()
        if error == errno.EPERM:
            print("mount被seccomp规则阻止: Operation not permitted")
        else:
            print(f"mount失败，错误码: {error}")
    else:
        print("mount调用成功")
except Exception as e:
    print(f"mount调用异常: {e}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert (
            "被seccomp规则阻止" in response.output
            or "Operation not permitted" in response.output
        )

    def test_chown_blocked(self, client):
        """测试chown系统调用被阻止"""
        code = """
import ctypes
import errno

# 尝试使用chown系统调用
libc = ctypes.CDLL(None)
chown = libc.chown
chown.argtypes = [ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint]
chown.restype = ctypes.c_int

try:
    # 尝试修改文件所有者
    result = chown(b"/tmp/test.txt", 1000, 1000)
    if result == -1:
        error = ctypes.get_errno()
        if error == errno.EPERM:
            print("chown被seccomp规则阻止: Operation not permitted")
        else:
            print(f"chown失败，错误码: {error}")
    else:
        print("chown调用成功")
except Exception as e:
    print(f"chown调用异常: {e}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert (
            "被seccomp规则阻止" in response.output
            or "Operation not permitted" in response.output
        )

    def test_symlink_blocked(self, client):
        """测试symlink系统调用被阻止"""
        code = """
import ctypes
import errno

# 尝试使用symlink系统调用
libc = ctypes.CDLL(None)
symlink = libc.symlink
symlink.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
symlink.restype = ctypes.c_int

try:
    # 尝试创建符号链接
    result = symlink(b"/tmp/target", b"/tmp/link")
    if result == -1:
        error = ctypes.get_errno()
        if error == errno.EPERM:
            print("symlink被seccomp规则阻止: Operation not permitted")
        else:
            print(f"symlink失败，错误码: {error}")
    else:
        print("symlink调用成功")
except Exception as e:
    print(f"symlink调用异常: {e}")
"""
        response = client.execute_python_code(code)

        assert response.success, f"执行失败: {response.error}"
        assert (
            "被seccomp规则阻止" in response.output
            or "Operation not permitted" in response.output
        )


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
