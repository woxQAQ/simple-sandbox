#!/usr/bin/env python3
"""
Pytest 配置文件

提供全局的 fixtures 和测试配置
"""

import asyncio
import os
import tempfile
import pytest
from pathlib import Path
from typing import Generator, Dict
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# 设置测试环境变量
os.environ["TESTING"] = "1"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_work_dir():
    """临时工作目录（保持向后兼容）"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_env() -> Generator[Dict[str, str], None, None]:
    """模拟环境变量"""
    original_env = os.environ.copy()
    test_env = {
        "TEST_MODE": "true",
        "LOG_LEVEL": "DEBUG",
        "PYTHONPATH": str(Path(__file__).parent.parent / "src"),
    }
    os.environ.update(test_env)
    yield test_env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_python_code():
    """示例Python代码"""
    return """
print("Hello, World!")
result = 2 + 2
print(f"2 + 2 = {result}")
"""


@pytest.fixture
def sample_nodejs_code():
    """示例Node.js代码"""
    return """
console.log("Hello, World!");
const result = 2 + 2;
console.log(`2 + 2 = ${result}`);
"""


@pytest.fixture
def python_runtime():
    """创建 Python 运行时实例"""
    try:
        from src.runtime.python_runtime import PythonRuntime

        return PythonRuntime()
    except ImportError:
        pytest.skip("Python runtime not available")


@pytest.fixture
def nodejs_runtime():
    """创建 Node.js 运行时实例"""
    try:
        from src.runtime.nodejs_runtime import NodeJSRuntime

        return NodeJSRuntime()
    except ImportError:
        pytest.skip("Node.js runtime not available")


@pytest.fixture
def runtime_manager():
    """创建运行时管理器实例"""
    try:
        from src.runtime.manager import RuntimeManager

        return RuntimeManager()
    except ImportError:
        pytest.skip("Runtime manager not available")


@pytest.fixture
def seccomp_manager():
    """创建 Seccomp 管理器实例"""
    try:
        from src.security.seccomp_manager import SeccompManager

        return SeccompManager()
    except ImportError:
        pytest.skip("Seccomp manager not available")


@pytest.fixture
def malicious_python_code():
    """恶意Python代码样例"""
    return """
import os
import subprocess

# 尝试访问文件系统
try:
    os.listdir('/')
    print("File system access successful")
except:
    print("File system access blocked")

# 尝试执行系统命令
try:
    subprocess.run(['ls', '-la'], capture_output=True)
    print("Command execution successful")
except:
    print("Command execution blocked")
"""


@pytest.fixture
def malicious_nodejs_code():
    """恶意Node.js代码样例"""
    return """
const fs = require('fs');
const { exec } = require('child_process');

// 尝试访问文件系统
try {
    fs.readdirSync('/');
    console.log("File system access successful");
} catch (e) {
    console.log("File system access blocked");
}

// 尝试执行系统命令
try {
    exec('ls -la', (error, stdout, stderr) => {
        if (error) {
            console.log("Command execution blocked");
        } else {
            console.log("Command execution successful");
        }
    });
} catch (e) {
    console.log("Command execution blocked");
}
"""


@pytest.fixture
def sample_python_error_code() -> str:
    """会产生错误的 Python 代码"""
    return """
print("This will cause an error")
raise ValueError("Test error")
"""


@pytest.fixture
def sample_nodejs_error_code() -> str:
    """会产生错误的 Node.js 代码"""
    return """
console.log("This will cause an error");
throw new Error("Test error");
"""


@pytest.fixture
def sample_timeout_code() -> str:
    """会超时的代码"""
    return """
import time
time.sleep(10)  # 超过默认超时时间
print("This should not be printed")
"""


@pytest.fixture
def sample_memory_intensive_code() -> str:
    """内存密集型代码"""
    return """
# 创建大量数据
data = []
for i in range(1000000):
    data.append(f"item_{i}" * 100)
print(f"Created {len(data)} items")
"""


@pytest.fixture
def sample_dangerous_python_code() -> str:
    """危险的 Python 代码"""
    return """
import os
import subprocess

# 尝试执行系统命令
os.system("ls -la")
subprocess.run(["whoami"])

# 尝试访问文件系统
with open("/etc/passwd", "r") as f:
    print(f.read())
"""


@pytest.fixture
def sample_dangerous_nodejs_code() -> str:
    """危险的 Node.js 代码"""
    return """
const fs = require('fs');
const { exec } = require('child_process');

// 尝试执行系统命令
exec('ls -la', (error, stdout, stderr) => {
    console.log(stdout);
});

// 尝试访问文件系统
fs.readFile('/etc/passwd', 'utf8', (err, data) => {
    if (!err) console.log(data);
});
"""


@pytest.fixture
def api_client():
    """FastAPI测试客户端"""
    try:
        from src.api.app import app

        return TestClient(app)
    except ImportError:
        pytest.skip("API app not available")


@pytest.fixture
def mock_subprocess():
    """模拟 subprocess 调用"""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(
            returncode=0, stdout="Mock output", stderr=""
        )
        yield mock_run


@pytest.fixture
def mock_docker():
    """模拟 Docker 调用"""
    with patch("docker.from_env") as mock_docker:
        mock_client = Mock()
        mock_container = Mock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"Mock container output"
        mock_client.containers.run.return_value = mock_container
        mock_docker.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_process_manager():
    """模拟进程管理器"""
    with patch("src.runtime.manager.ProcessManager") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_security_manager():
    """模拟安全管理器"""
    with patch("src.security.SecurityManager") as mock:
        mock_instance = Mock()
        mock_instance.is_seccomp_supported.return_value = True
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_file_system(temp_dir):
    """模拟文件系统操作"""
    # 创建模拟的配置文件
    config_dir = temp_dir / "config"
    config_dir.mkdir()

    # Python seccomp 配置
    python_config = {
        "default_action": "SCMP_ACT_KILL",
        "allowed_syscalls": [
            "read",
            "write",
            "open",
            "close",
            "stat",
            "fstat",
            "lstat",
            "poll",
            "lseek",
            "mmap",
            "mprotect",
            "munmap",
            "brk",
            "rt_sigaction",
            "rt_sigprocmask",
            "rt_sigreturn",
            "ioctl",
            "pread64",
            "pwrite64",
            "readv",
            "writev",
            "access",
            "pipe",
            "select",
            "sched_yield",
            "mremap",
            "exit",
            "exit_group",
            "getpid",
            "getuid",
            "getgid",
        ],
    }

    import json

    with open(config_dir / "python.json", "w") as f:
        json.dump(python_config, f, indent=2)

    # Node.js seccomp 配置
    nodejs_config = {
        "default_action": "SCMP_ACT_KILL",
        "allowed_syscalls": [
            "read",
            "write",
            "open",
            "close",
            "stat",
            "fstat",
            "lstat",
            "poll",
            "lseek",
            "mmap",
            "mprotect",
            "munmap",
            "brk",
            "rt_sigaction",
            "rt_sigprocmask",
            "rt_sigreturn",
            "ioctl",
            "pread64",
            "pwrite64",
            "readv",
            "writev",
            "access",
            "pipe",
            "select",
            "sched_yield",
            "mremap",
            "exit",
            "exit_group",
            "getpid",
            "getuid",
            "getgid",
        ],
    }

    with open(config_dir / "nodejs.json", "w") as f:
        json.dump(nodejs_config, f, indent=2)

    # 模拟配置路径
    with patch(
        "src.security.seccomp_manager.SeccompManager._get_config_path"
    ) as mock_path:
        mock_path.return_value = config_dir
        yield config_dir


@pytest.fixture
def resource_limits():
    """资源限制配置"""
    from src.runtime.models import ResourceLimits

    return ResourceLimits(
        max_memory_mb=64,
        max_cpu_time_seconds=10,
        max_processes=3,
        max_file_size_mb=5,
        max_files=50,
    )


@pytest.fixture(scope="session")
def is_linux():
    """检查是否为Linux环境"""
    import platform

    return platform.system().lower() == "linux"


@pytest.fixture(autouse=True)
def setup_test_environment(mock_env):
    """自动设置测试环境"""
    # 确保测试环境变量已设置
    pass


@pytest.fixture
def capture_logs(caplog):
    """捕获日志输出"""
    import logging

    caplog.set_level(logging.DEBUG)
    return caplog


# 异步测试支持
@pytest.fixture
def anyio_backend():
    """指定 anyio 后端"""
    return "asyncio"


# 测试标记配置
pytest_plugins = []


def pytest_configure(config):
    """Pytest 配置"""
    # 注册自定义标记
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "e2e: 端到端测试")
    config.addinivalue_line("markers", "security: 安全测试")
    config.addinivalue_line("markers", "performance: 性能测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "linux_only: 仅Linux环境测试")


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    import platform

    # 为测试添加默认标记
    for item in items:
        # 根据文件路径添加标记
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)  # 性能测试通常较慢

    # 根据环境跳过特定测试
    if platform.system().lower() != "linux":
        skip_linux = pytest.mark.skip(reason="需要Linux环境")
        for item in items:
            if "linux_only" in item.keywords:
                item.add_marker(skip_linux)
