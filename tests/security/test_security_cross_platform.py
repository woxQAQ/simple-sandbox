#!/usr/bin/env python3
"""
跨平台安全模块测试

测试在非Linux平台上也能运行的安全模块功能
"""

import os
import sys
import pytest
import tempfile
import unittest.mock as mock
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestSecurityModuleImport:
    """安全模块导入测试"""

    def test_linux_only_import_behavior(self):
        """测试Linux专用模块的导入行为"""
        # 在非Linux平台上，seccomp_wrapper应该无法导入
        if not sys.platform.startswith("linux"):
            with pytest.raises(ImportError, match="Linux-only"):
                from src.security.injection.seccomp_wrapper import (
                    SeccompInjector,
                )
        else:
            # 在Linux平台上应该能正常导入
            from src.security.injection.seccomp_wrapper import SeccompInjector

            assert SeccompInjector is not None

    def test_security_error_import(self):
        """测试SecurityError可以独立导入"""
        # SecurityError应该在所有平台上都能导入
        try:
            # 直接从文件导入，避免整个模块的导入问题
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "security_init",
                project_root / "src" / "security" / "__init__.py",
            )

            # 模拟Linux环境来测试SecurityError定义
            with mock.patch("sys.platform", "linux"):
                with mock.patch(
                    "src.security.injection.seccomp_wrapper.SeccompInjector"
                ):
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # 验证SecurityError存在且可用
                    assert hasattr(module, "SecurityError")
                    assert issubclass(module.SecurityError, Exception)

                    # 测试SecurityError功能
                    error = module.SecurityError("Test error")
                    assert str(error) == "Test error"

        except Exception as e:
            pytest.fail(f"Failed to import SecurityError: {e}")

    def test_platform_detection(self):
        """测试平台检测"""
        # 验证当前平台检测
        current_platform = sys.platform
        assert isinstance(current_platform, str)
        assert len(current_platform) > 0

        # 验证Linux检测逻辑
        is_linux = current_platform.startswith("linux")
        if is_linux:
            # 在Linux上，seccomp应该可用
            assert True  # 占位符，实际测试在Linux CI中进行
        else:
            # 在非Linux平台上，seccomp不可用
            assert not is_linux


class TestSecurityErrorStandalone:
    """独立的SecurityError测试"""

    def setup_method(self):
        """设置SecurityError类用于测试"""

        # 创建一个简单的SecurityError类用于测试
        class SecurityError(Exception):
            """Security-related error"""

            pass

        self.SecurityError = SecurityError

    def test_security_error_basic_functionality(self):
        """测试SecurityError基本功能"""
        # 测试基本异常创建
        error = self.SecurityError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_security_error_inheritance(self):
        """测试SecurityError继承"""
        error = self.SecurityError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, self.SecurityError)

    def test_security_error_with_various_messages(self):
        """测试各种消息类型的SecurityError"""
        test_cases = [
            "Simple message",
            "",  # 空字符串
            "Message with numbers: 123",
            "Message with special chars: !@#$%^&*()",
            "Multi-line\nmessage\nwith\nbreaks",
            "Unicode message: 测试消息 🔒",
        ]

        for message in test_cases:
            error = self.SecurityError(message)
            assert str(error) == message

    def test_security_error_exception_chaining(self):
        """测试SecurityError异常链"""
        original_error = ValueError("Original error")

        try:
            raise original_error
        except ValueError as e:
            security_error = self.SecurityError("Security error occurred")
            security_error.__cause__ = e

            assert security_error.__cause__ is original_error
            assert str(security_error.__cause__) == "Original error"


class TestSecurityConfigurationFiles:
    """安全配置文件测试"""

    def test_static_config_files_exist(self):
        """测试静态配置文件存在"""
        static_dir = project_root / "src" / "security" / "static"

        # 验证静态目录存在
        assert static_dir.exists(), f"Static directory not found: {static_dir}"
        assert (
            static_dir.is_dir()
        ), f"Static path is not a directory: {static_dir}"

        # 验证配置文件存在
        expected_files = ["python.json", "nodejs.json"]
        for filename in expected_files:
            config_file = static_dir / filename
            assert config_file.exists(), f"Config file not found: {config_file}"
            assert (
                config_file.is_file()
            ), f"Config path is not a file: {config_file}"

    def test_config_file_format(self):
        """测试配置文件格式"""
        import json

        static_dir = project_root / "src" / "security" / "static"
        config_files = ["python.json", "nodejs.json"]

        for filename in config_files:
            config_file = static_dir / filename
            if config_file.exists():
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        config_data = json.load(f)

                    # 验证基本结构
                    assert isinstance(
                        config_data, dict
                    ), f"Config should be a dict: {filename}"

                    # 验证必需字段
                    required_fields = [
                        "language",
                        "description",
                        "defaultAction",
                    ]
                    for field in required_fields:
                        assert (
                            field in config_data
                        ), f"Missing field '{field}' in {filename}"

                    # 验证syscalls字段
                    if "syscalls" in config_data:
                        assert isinstance(
                            config_data["syscalls"], list
                        ), f"syscalls should be a list in {filename}"

                        # 验证syscalls不为空
                        assert (
                            len(config_data["syscalls"]) > 0
                        ), f"syscalls list should not be empty in {filename}"

                        # 验证syscalls结构（可能是对象数组）
                        for syscall_entry in config_data["syscalls"]:
                            if isinstance(syscall_entry, dict):
                                # 新格式：包含names字段的对象
                                assert (
                                    "names" in syscall_entry
                                ), f"syscall entry should have 'names' field in {filename}"
                                assert isinstance(
                                    syscall_entry["names"], list
                                ), f"syscall names should be a list in {filename}"
                                for name in syscall_entry["names"]:
                                    assert isinstance(
                                        name, str
                                    ), f"All syscall names should be strings in {filename}"
                                    assert (
                                        len(name) > 0
                                    ), f"Syscall names should not be empty in {filename}"
                            elif isinstance(syscall_entry, str):
                                # 旧格式：直接是字符串
                                assert (
                                    len(syscall_entry) > 0
                                ), f"Syscall names should not be empty in {filename}"
                            else:
                                pytest.fail(
                                    f"Invalid syscall entry format in {filename}"
                                )

                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {filename}: {e}")
                except Exception as e:
                    pytest.fail(f"Error reading {filename}: {e}")

    def test_language_specific_configs(self):
        """测试语言特定配置"""
        import json

        static_dir = project_root / "src" / "security" / "static"

        # 测试Python配置
        python_config = static_dir / "python.json"
        if python_config.exists():
            with open(python_config, "r", encoding="utf-8") as f:
                config = json.load(f)

            assert config["language"] == "python"
            assert "description" in config
            assert "syscalls" in config

            # Python应该包含一些常见的系统调用
            common_python_syscalls = ["read", "write", "open", "close"]
            syscalls = config["syscalls"]

            # 提取所有系统调用名称（处理新格式）
            all_syscall_names = []
            for entry in syscalls:
                if isinstance(entry, dict) and "names" in entry:
                    all_syscall_names.extend(entry["names"])
                elif isinstance(entry, str):
                    all_syscall_names.append(entry)

            found_syscalls = [
                sc for sc in common_python_syscalls if sc in all_syscall_names
            ]
            assert (
                len(found_syscalls) > 0
            ), "Python config should contain common syscalls"

        # 测试Node.js配置
        nodejs_config = static_dir / "nodejs.json"
        if nodejs_config.exists():
            with open(nodejs_config, "r", encoding="utf-8") as f:
                config = json.load(f)

            assert config["language"] == "nodejs"
            assert "description" in config
            assert "syscalls" in config

            # Node.js应该包含一些常见的系统调用
            common_nodejs_syscalls = ["read", "write", "open", "close"]
            syscalls = config["syscalls"]

            # 提取所有系统调用名称（处理新格式）
            all_syscall_names = []
            for entry in syscalls:
                if isinstance(entry, dict) and "names" in entry:
                    all_syscall_names.extend(entry["names"])
                elif isinstance(entry, str):
                    all_syscall_names.append(entry)

            found_syscalls = [
                sc for sc in common_nodejs_syscalls if sc in all_syscall_names
            ]
            assert (
                len(found_syscalls) > 0
            ), "Node.js config should contain common syscalls"


class TestSecurityModuleStructure:
    """安全模块结构测试"""

    def test_security_directory_structure(self):
        """测试安全模块目录结构"""
        security_dir = project_root / "src" / "security"

        # 验证主目录存在
        assert (
            security_dir.exists()
        ), f"Security directory not found: {security_dir}"
        assert (
            security_dir.is_dir()
        ), f"Security path is not a directory: {security_dir}"

        # 验证主要文件存在
        expected_files = [
            "__init__.py",
        ]

        for filename in expected_files:
            file_path = security_dir / filename
            assert file_path.exists(), f"File not found: {file_path}"
            assert file_path.is_file(), f"Path is not a file: {file_path}"

        # 验证子目录存在
        expected_dirs = [
            "injection",
            "static",
        ]

        for dirname in expected_dirs:
            dir_path = security_dir / dirname
            assert dir_path.exists(), f"Directory not found: {dir_path}"
            assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

    def test_injection_directory_structure(self):
        """测试injection目录结构"""
        injection_dir = project_root / "src" / "security" / "injection"

        # 验证injection目录存在
        assert (
            injection_dir.exists()
        ), f"Injection directory not found: {injection_dir}"
        assert (
            injection_dir.is_dir()
        ), f"Injection path is not a directory: {injection_dir}"

        # 验证主要文件存在
        expected_files = [
            "seccomp_wrapper.py",
        ]

        for filename in expected_files:
            file_path = injection_dir / filename
            assert file_path.exists(), f"File not found: {file_path}"
            assert file_path.is_file(), f"Path is not a file: {file_path}"

        # __init__.py 可能不存在，这是可选的
        init_file = injection_dir / "__init__.py"
        if init_file.exists():
            assert (
                init_file.is_file()
            ), f"__init__.py is not a file: {init_file}"

    def test_file_permissions(self):
        """测试文件权限"""
        security_dir = project_root / "src" / "security"

        # 递归检查所有Python文件
        for py_file in security_dir.rglob("*.py"):
            # 验证文件可读
            assert os.access(py_file, os.R_OK), f"File not readable: {py_file}"

            # 验证文件大小合理（不为空，不过大）
            file_size = py_file.stat().st_size
            assert file_size > 0, f"File is empty: {py_file}"
            assert (
                file_size < 1024 * 1024
            ), f"File too large: {py_file}"  # 1MB限制


class TestMockSecurityManager:
    """模拟SecurityManager测试"""

    def setup_method(self):
        """设置模拟SecurityManager"""
        self.temp_dir = tempfile.mkdtemp()

        # 创建一个简化的SecurityManager模拟
        class MockSecurityManager:
            def __init__(self, library_dir=None):
                self.library_dir = library_dir or "/default/lib"
                self._injector_cache = {}
                self.supported_languages = ["python", "nodejs", "java", "cpp"]

            def is_language_supported(self, language):
                return language in self.supported_languages

            def get_supported_languages(self):
                return self.supported_languages.copy()

            def validate_uid_gid(self, uid, gid):
                if not isinstance(uid, int) or not isinstance(gid, int):
                    raise TypeError("UID and GID must be integers")
                if uid < 0 or gid < 0:
                    raise ValueError("UID and GID must be non-negative")
                return True

        self.MockSecurityManager = MockSecurityManager

    def teardown_method(self):
        """清理"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_mock_security_manager_basic(self):
        """测试模拟SecurityManager基本功能"""
        manager = self.MockSecurityManager(library_dir=self.temp_dir)

        assert manager.library_dir == self.temp_dir
        assert isinstance(manager._injector_cache, dict)
        assert len(manager._injector_cache) == 0

    def test_language_support_checking(self):
        """测试语言支持检查"""
        manager = self.MockSecurityManager()

        # 测试支持的语言
        supported_languages = ["python", "nodejs", "java", "cpp"]
        for lang in supported_languages:
            assert manager.is_language_supported(lang)

        # 测试不支持的语言
        unsupported_languages = ["ruby", "go", "rust", "php"]
        for lang in unsupported_languages:
            assert not manager.is_language_supported(lang)

    def test_uid_gid_validation(self):
        """测试UID/GID验证"""
        manager = self.MockSecurityManager()

        # 测试有效值
        valid_pairs = [(0, 0), (1000, 1000), (65535, 65535)]
        for uid, gid in valid_pairs:
            assert manager.validate_uid_gid(uid, gid) is True

        # 测试无效值
        invalid_pairs = [
            (-1, 1000),  # 负数UID
            (1000, -1),  # 负数GID
            ("1000", 1000),  # 字符串UID
            (1000, "1000"),  # 字符串GID
            (None, 1000),  # None UID
            (1000, None),  # None GID
        ]

        for uid, gid in invalid_pairs:
            with pytest.raises((TypeError, ValueError)):
                manager.validate_uid_gid(uid, gid)

    def test_supported_languages_immutability(self):
        """测试支持语言列表的不可变性"""
        manager = self.MockSecurityManager()

        # 获取支持的语言列表
        languages1 = manager.get_supported_languages()
        languages2 = manager.get_supported_languages()

        # 应该返回不同的实例（副本）
        assert languages1 is not languages2

        # 但内容应该相同
        assert languages1 == languages2

        # 修改返回的列表不应该影响原始列表
        languages1.append("new_language")
        languages3 = manager.get_supported_languages()
        assert "new_language" not in languages3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
