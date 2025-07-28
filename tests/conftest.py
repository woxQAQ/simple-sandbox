#!/usr/bin/env python3
"""
pytest配置文件

提供测试的公共配置、fixtures和工具函数
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """项目根目录路径"""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_directory():
    """临时目录fixture"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_library_dir(temp_directory):
    """模拟的库文件目录"""
    lib_dir = os.path.join(temp_directory, "lib")
    os.makedirs(lib_dir, exist_ok=True)
    return lib_dir


@pytest.fixture
def mock_seccomp_injector():
    """模拟的SeccompInjector"""
    mock_injector = MagicMock()
    mock_injector.inject_seccomp_profile.return_value = None
    mock_injector.setup_no_new_privs.return_value = None
    mock_injector.drop_privileges.return_value = None
    mock_injector.apply_seccomp_filter.return_value = None
    mock_injector.get_error_description.return_value = "Mock error description"
    mock_injector.is_supported.return_value = True
    return mock_injector


@pytest.fixture
def skip_if_not_linux():
    """如果不是Linux系统则跳过测试"""
    if not sys.platform.startswith("linux"):
        pytest.skip("This test requires Linux platform")


@pytest.fixture
def mock_ctypes_cdll():
    """模拟ctypes.CDLL"""
    with patch("ctypes.CDLL") as mock_cdll:
        mock_lib = MagicMock()
        mock_cdll.return_value = mock_lib

        # 设置函数签名
        mock_lib.inject_seccomp_profile.return_value = 0
        mock_lib.setup_no_new_privs.return_value = 0
        mock_lib.drop_privileges.return_value = 0
        mock_lib.apply_seccomp_filter.return_value = 0

        yield mock_lib


@pytest.fixture
def sample_syscall_config():
    """示例系统调用配置"""
    return {
        "language": "python",
        "description": "Python语言的系统调用白名单配置",
        "defaultAction": "SCMP_ACT_ERRNO",
        "architectures": ["SCMP_ARCH_X86_64"],
        "syscalls": [
            {
                "names": ["read", "write", "open", "close"],
                "action": "SCMP_ACT_ALLOW",
            }
        ],
    }


# pytest配置
def pytest_configure(config):
    """pytest配置"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "linux_only: mark test as requiring Linux platform"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security-related test"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 为Linux专用测试添加跳过标记
    linux_only = pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="requires Linux platform"
    )

    for item in items:
        if "linux_only" in item.keywords:
            item.add_marker(linux_only)


# 测试工具函数
def create_mock_library_file(directory: str, language: str) -> str:
    """创建模拟的库文件"""
    filename = f"libseccomp_injector_{language}.so"
    filepath = os.path.join(directory, filename)

    # 创建空文件
    with open(filepath, "w") as f:
        f.write("# Mock library file")

    return filepath


def assert_security_error_raised(func, *args, **kwargs):
    """断言抛出SecurityError异常"""
    try:
        from src.security import SecurityError

        with pytest.raises(SecurityError):
            func(*args, **kwargs)
    except ImportError:
        pytest.skip("Security module not available")


def assert_seccomp_injection_error_raised(func, *args, **kwargs):
    """断言抛出SeccompInjectionError异常"""
    try:
        from src.security import SeccompInjectionError

        with pytest.raises(SeccompInjectionError):
            func(*args, **kwargs)
    except ImportError:
        pytest.skip("Security module not available")
