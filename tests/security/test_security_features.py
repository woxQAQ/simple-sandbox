#!/usr/bin/env python3
"""
安全功能测试
测试沙箱的安全机制和防护功能
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.security.seccomp_manager import SeccompManager


class TestSecurityFeatures:
    """安全功能测试"""

    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def seccomp_manager(self):
        """Seccomp管理器"""
        return SeccompManager()

    @pytest.mark.security
    def test_dangerous_imports_blocked(self, client):
        """测试危险导入被阻止"""
        dangerous_codes = [
            # 操作系统相关
            "import os; os.system('ls')",
            "import subprocess; subprocess.run(['ls'])",
            "import shutil; shutil.rmtree('/')",
            # 网络相关
            "import socket; socket.socket()",
            "import urllib.request; urllib.request.urlopen('http://example.com')",
            "import requests; requests.get('http://example.com')",
            # 文件系统相关
            "open('/etc/passwd', 'r').read()",
            "import pathlib; pathlib.Path('/etc').iterdir()",
            # 进程相关
            "import multiprocessing; multiprocessing.Process()",
            "import threading; threading.Thread()",
            # 系统信息
            "import platform; platform.system()",
            "import getpass; getpass.getuser()",
        ]

        for code in dangerous_codes:
            request_data = {
                "language": "python",
                "code": code,
                "timeout": 30,
                "memory_limit": 128,
            }

            response = client.post("/api/v1/execute", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # 应该被阻止或产生错误
            assert data["status"] in ["error", "blocked"]
            if data["status"] == "error":
                error_msg = (
                    data["stderr"] + " " + (data["error"] or "")
                ).lower()
                # 检查是否包含安全相关的错误信息
                security_keywords = [
                    "import",
                    "module",
                    "permission",
                    "denied",
                    "blocked",
                ]
                assert any(
                    keyword in error_msg for keyword in security_keywords
                )

    @pytest.mark.security
    def test_dangerous_functions_blocked(self, client):
        """测试危险函数被阻止"""
        dangerous_codes = [
            # 执行系统命令
            "exec('import os; os.system(\"ls\")')",
            'eval(\'__import__("os").system("ls")\')',
            "compile('import os', '<string>', 'exec')",
            # 访问内置函数
            "__import__('os').system('ls')",
            "getattr(__builtins__, 'exec')('import os')",
            # 文件操作
            "open('/etc/passwd').read()",
            "file('/etc/passwd').read()",
            # 网络操作
            "__import__('urllib.request').urlopen('http://example.com')",
            "__import__('socket').socket()",
        ]

        for code in dangerous_codes:
            request_data = {
                "language": "python",
                "code": code,
                "timeout": 30,
                "memory_limit": 128,
            }

            response = client.post("/api/v1/execute", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # 应该被阻止或产生错误
            assert data["status"] in ["error", "blocked"]

    @pytest.mark.security
    def test_nodejs_dangerous_operations_blocked(self, client):
        """测试Node.js危险操作被阻止"""
        dangerous_codes = [
            # 文件系统操作
            "const fs = require('fs'); fs.readFileSync('/etc/passwd');",
            "require('fs').writeFileSync('/tmp/test', 'data');",
            # 进程操作
            "const { exec } = require('child_process'); exec('ls');",
            "require('child_process').spawn('ls');",
            # 网络操作
            "const http = require('http'); http.get('http://example.com');",
            "require('net').createServer();",
            # 操作系统操作
            "const os = require('os'); os.userInfo();",
            "require('process').exit(1);",
        ]

        for code in dangerous_codes:
            request_data = {
                "language": "nodejs",
                "code": code,
                "timeout": 30,
                "memory_limit": 128,
            }

            response = client.post("/api/v1/execute", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # 应该被阻止或产生错误
            assert data["status"] in ["error", "blocked"]

    @pytest.mark.security
    def test_memory_limit_enforcement(self, client):
        """测试内存限制强制执行"""
        # 尝试分配大量内存
        memory_bomb_code = """
# 尝试分配大量内存
data = []
try:
    for i in range(1000000):
        data.append([0] * 1000)  # 每次分配1000个整数
        if i % 10000 == 0:
            print(f"Allocated {i} arrays")
except MemoryError:
    print("Memory limit reached")
print(f"Final arrays count: {len(data)}")
"""

        request_data = {
            "language": "python",
            "code": memory_bomb_code,
            "timeout": 60,
            "memory_limit": 64,  # 较小的内存限制
        }

        response = client.post("/api/v1/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 应该因内存限制而失败或被限制
        if data["status"] == "error":
            error_msg = (data["stderr"] + " " + (data["error"] or "")).lower()
            assert "memory" in error_msg or "killed" in error_msg
        elif data["status"] == "success":
            # 如果成功，内存使用应该在限制范围内
            assert (
                data["memory_used"] <= 64 * 1024 * 1024 * 1.1
            )  # 允许10%的误差

    @pytest.mark.security
    def test_timeout_enforcement(self, client):
        """测试超时限制强制执行"""
        # 无限循环代码
        infinite_loop_code = """
import time
count = 0
while True:
    count += 1
    if count % 1000000 == 0:
        print(f"Count: {count}")
    # 短暂休眠避免CPU 100%
    if count % 10000000 == 0:
        time.sleep(0.001)
"""

        request_data = {
            "language": "python",
            "code": infinite_loop_code,
            "timeout": 5,  # 5秒超时
            "memory_limit": 128,
        }

        response = client.post("/api/v1/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 应该因超时而终止
        assert data["status"] == "timeout"
        assert data["execution_time"] >= 5.0
        assert data["execution_time"] <= 10.0  # 允许一些误差
        assert data["error"] is not None

    @pytest.mark.security
    def test_file_system_isolation(self, client):
        """测试文件系统隔离"""
        # 尝试访问系统文件
        file_access_codes = [
            "print(open('/etc/passwd').read())",
            "print(open('/proc/version').read())",
            "import os; print(os.listdir('/'))",
            "import glob; print(glob.glob('/etc/*'))",
        ]

        for code in file_access_codes:
            request_data = {
                "language": "python",
                "code": code,
                "timeout": 30,
                "memory_limit": 128,
            }

            response = client.post("/api/v1/execute", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # 应该被阻止或产生权限错误
            assert data["status"] in ["error", "blocked"]
            if data["status"] == "error":
                error_msg = (
                    data["stderr"] + " " + (data["error"] or "")
                ).lower()
                permission_keywords = [
                    "permission",
                    "denied",
                    "no such file",
                    "not found",
                ]
                assert any(
                    keyword in error_msg for keyword in permission_keywords
                )

    @pytest.mark.security
    def test_network_isolation(self, client):
        """测试网络隔离"""
        # 尝试网络连接
        network_codes = [
            """
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('google.com', 80))
    print("Network connection successful")
except Exception as e:
    print(f"Network error: {e}")
""",
            """
import urllib.request
try:
    response = urllib.request.urlopen('http://httpbin.org/ip')
    print(response.read().decode())
except Exception as e:
    print(f"HTTP error: {e}")
""",
        ]

        for code in network_codes:
            request_data = {
                "language": "python",
                "code": code,
                "timeout": 30,
                "memory_limit": 128,
            }

            response = client.post("/api/v1/execute", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # 网络应该被阻止
            if data["status"] == "success":
                output = data["stdout"].lower()
                # 应该显示网络错误而不是成功连接
                assert "network error" in output or "http error" in output
                assert "network connection successful" not in output

    @pytest.mark.security
    def test_process_isolation(self, client):
        """测试进程隔离"""
        # 尝试创建子进程
        process_codes = [
            """
import subprocess
try:
    result = subprocess.run(['ls', '/'], capture_output=True, text=True)
    print(f"Command output: {result.stdout}")
except Exception as e:
    print(f"Process error: {e}")
""",
            """
import os
try:
    result = os.system('echo "Hello from system"')
    print(f"System call result: {result}")
except Exception as e:
    print(f"System error: {e}")
""",
        ]

        for code in process_codes:
            request_data = {
                "language": "python",
                "code": code,
                "timeout": 30,
                "memory_limit": 128,
            }

            response = client.post("/api/v1/execute", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # 进程创建应该被阻止
            assert data["status"] in ["error", "blocked"]

    @pytest.mark.security
    def test_seccomp_configuration_loading(self, seccomp_manager):
        """测试Seccomp配置加载"""
        # 测试Python配置
        python_config = seccomp_manager.load_config("python")
        assert python_config is not None
        assert "default_action" in python_config
        assert "allowed_syscalls" in python_config

        # 测试Node.js配置
        nodejs_config = seccomp_manager.load_config("nodejs")
        assert nodejs_config is not None
        assert "default_action" in nodejs_config
        assert "allowed_syscalls" in nodejs_config

        # 测试不支持的语言
        with pytest.raises(ValueError):
            seccomp_manager.load_config("unsupported_language")

    @pytest.mark.security
    def test_seccomp_syscall_filtering(self, seccomp_manager):
        """测试Seccomp系统调用过滤"""
        # 加载Python配置
        python_config = seccomp_manager.load_config("python")
        allowed_syscalls = python_config["allowed_syscalls"]

        # 验证基本系统调用被允许
        basic_syscalls = ["read", "write", "exit", "exit_group"]
        for syscall in basic_syscalls:
            if syscall in allowed_syscalls:
                assert seccomp_manager.is_syscall_allowed("python", syscall)

        # 验证危险系统调用被禁止
        dangerous_syscalls = ["execve", "fork", "clone", "socket", "connect"]
        for syscall in dangerous_syscalls:
            if syscall not in allowed_syscalls:
                assert not seccomp_manager.is_syscall_allowed("python", syscall)

    @pytest.mark.security
    def test_input_validation_security(self, client):
        """测试输入验证安全性"""
        # 测试恶意输入
        malicious_inputs = [
            # 代码注入尝试
            {
                "language": "python",
                "code": "'; import os; os.system('rm -rf /'); #",
                "timeout": 30,
                "memory_limit": 128,
            },
            # 超长代码
            {
                "language": "python",
                "code": "print('x')" * 10000,
                "timeout": 30,
                "memory_limit": 128,
            },
            # 特殊字符
            {
                "language": "python",
                "code": "print('\x00\x01\x02')",
                "timeout": 30,
                "memory_limit": 128,
            },
        ]

        for request_data in malicious_inputs:
            response = client.post("/api/v1/execute", json=request_data)

            # 应该被正确处理，不会导致系统崩溃
            assert response.status_code in [200, 422]  # 200或验证错误

            if response.status_code == 200:
                data = response.json()
                # 如果执行，应该安全地处理
                assert "status" in data

    @pytest.mark.security
    def test_environment_variable_isolation(self, client):
        """测试环境变量隔离"""
        # 尝试访问系统环境变量
        code = """
import os
print("Environment variables:")
for key, value in os.environ.items():
    print(f"{key}: {value}")
"""

        request_data = {
            "language": "python",
            "code": code,
            "timeout": 30,
            "memory_limit": 128,
        }

        response = client.post("/api/v1/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        if data["status"] == "success":
            output = data["stdout"]
            # 不应该包含敏感的系统环境变量
            sensitive_vars = ["PATH", "HOME", "USER", "PWD"]
            for var in sensitive_vars:
                # 如果包含这些变量，它们应该是沙箱化的值
                if var in output:
                    # 检查值是否被适当隔离
                    lines = output.split("\n")
                    for line in lines:
                        if f"{var}:" in line:
                            # 值不应该包含真实的系统路径
                            assert "/home/" not in line.lower()
                            assert "/root/" not in line.lower()

    @pytest.mark.security
    def test_resource_exhaustion_protection(self, client):
        """测试资源耗尽保护"""
        # CPU密集型代码
        cpu_intensive_code = """
count = 0
for i in range(10000000):
    count += i * i
print(f"Final count: {count}")
"""

        request_data = {
            "language": "python",
            "code": cpu_intensive_code,
            "timeout": 10,
            "memory_limit": 128,
        }

        response = client.post("/api/v1/execute", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 应该在合理时间内完成或超时
        assert data["status"] in ["success", "timeout"]
        if data["status"] == "success":
            assert data["execution_time"] <= 10
        elif data["status"] == "timeout":
            assert data["execution_time"] >= 10

    @pytest.mark.security
    def test_code_injection_prevention(self, client):
        """测试代码注入防护"""
        # 尝试各种代码注入
        injection_attempts = [
            # Python代码注入
            "exec(__import__('os').system('ls'))",
            'eval(\'__import__("subprocess").call(["ls"])\')',
            "compile('import os; os.system(\"ls\")', '<string>', 'exec')",
            # 字符串操作注入
            "''.join([chr(i) for i in [105, 109, 112, 111, 114, 116, 32, 111, 115]])",  # 'import os'
            # 属性访问注入
            "getattr(__builtins__, 'exec')('import os')",
            "setattr(__builtins__, 'x', __import__('os'))",
        ]

        for code in injection_attempts:
            request_data = {
                "language": "python",
                "code": code,
                "timeout": 30,
                "memory_limit": 128,
            }

            response = client.post("/api/v1/execute", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # 注入尝试应该被阻止
            assert data["status"] in ["error", "blocked"]

    @pytest.mark.security
    @pytest.mark.linux_only
    def test_container_escape_prevention(self, client):
        """测试容器逃逸防护"""
        # 尝试容器逃逸技术
        escape_attempts = [
            # 尝试访问宿主机文件系统
            "import os; print(os.listdir('/proc/1/root'))",
            # 尝试访问Docker socket
            "import os; print(os.path.exists('/var/run/docker.sock'))",
            # 尝试访问特权设备
            "import os; print(os.listdir('/dev'))",
            # 尝试修改系统配置
            "open('/etc/hosts', 'a').write('127.0.0.1 evil.com')",
        ]

        for code in escape_attempts:
            request_data = {
                "language": "python",
                "code": code,
                "timeout": 30,
                "memory_limit": 128,
            }

            response = client.post("/api/v1/execute", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # 逃逸尝试应该被阻止
            assert data["status"] in ["error", "blocked"]
