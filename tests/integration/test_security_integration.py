"""
安全策略集成测试
测试seccomp系统调用过滤、权限管理、安全策略执行等功能
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.security import (
    SeccompInjectionError,
    SeccompInjector,
    SecurityError,
    SecurityManager,
    create_secure_process,
    inject_seccomp_for_language,
)


class TestSecurityManager:
    """安全管理器测试"""

    def setup_method(self):
        """测试前设置"""
        self.security_manager = SecurityManager()

    def test_is_seccomp_supported(self):
        """测试seccomp支持检查"""
        # 在Linux平台上应该返回True
        assert self.security_manager.is_seccomp_supported() is True

    @patch("src.security.SeccompInjector")
    def test_get_injector_for_language_success(self, mock_injector_class):
        """测试获取语言特定注入器成功"""
        mock_injector = Mock()
        mock_injector_class.return_value = mock_injector

        injector = self.security_manager._get_injector_for_language("python")
        assert injector == mock_injector
        mock_injector_class.assert_called_once_with(
            language="python", library_path=None
        )

    def test_get_injector_for_language_unsupported(self):
        """测试获取不支持语言的注入器"""
        with pytest.raises(SecurityError) as exc_info:
            self.security_manager._get_injector_for_language("unsupported_lang")
        assert "Unsupported language: unsupported_lang" in str(exc_info.value)

    @patch("src.security.SeccompInjector")
    def test_injector_caching(self, mock_injector_class):
        """测试注入器缓存机制"""
        mock_injector = Mock()
        mock_injector_class.return_value = mock_injector

        # 第一次调用
        injector1 = self.security_manager._get_injector_for_language("python")
        # 第二次调用应该返回缓存的实例
        injector2 = self.security_manager._get_injector_for_language("python")

        assert injector1 is injector2
        assert mock_injector_class.call_count == 1

    @patch("src.security.SeccompInjector")
    def test_setup_security_profile(self, mock_injector_class):
        """测试设置安全配置"""
        mock_injector = Mock()
        mock_injector_class.return_value = mock_injector

        self.security_manager.setup_security_profile("python", 1000, 1000)

        mock_injector.inject_seccomp_profile.assert_called_once_with(1000, 1000)

    @patch("src.security.SeccompInjector")
    def test_setup_no_new_privs(self, mock_injector_class):
        """测试设置NO_NEW_PRIVS"""
        mock_injector = Mock()
        mock_injector_class.return_value = mock_injector

        self.security_manager.setup_no_new_privs("python")

        mock_injector.setup_no_new_privs.assert_called_once()

    @patch("src.security.SeccompInjector")
    def test_drop_privileges(self, mock_injector_class):
        """测试权限降级"""
        mock_injector = Mock()
        mock_injector_class.return_value = mock_injector

        self.security_manager.drop_privileges("python", 1000, 1000)

        mock_injector.drop_privileges.assert_called_once_with(1000, 1000)

    @patch("src.security.SeccompInjector")
    def test_apply_seccomp_filter(self, mock_injector_class):
        """测试应用seccomp过滤器"""
        mock_injector = Mock()
        mock_injector_class.return_value = mock_injector

        self.security_manager.apply_seccomp_filter("python")

        mock_injector.apply_seccomp_filter.assert_called_once()


class TestSeccompInjector:
    """seccomp注入器测试"""

    def setup_method(self):
        """测试前设置"""
        # 创建模拟的库对象
        self.mock_lib = Mock()
        self.mock_lib.setup_no_new_privs.return_value = 0  # SECCOMP_SUCCESS
        self.mock_lib.drop_privileges.return_value = 0
        self.mock_lib.apply_seccomp_filter.return_value = 0
        self.mock_lib.inject_seccomp_profile.return_value = 0
        self.mock_lib.get_error_description.return_value = b"Success"

    @patch("src.security.injection.seccomp_wrapper.ctypes.CDLL")
    def test_injector_initialization_success(self, mock_cdll):
        """测试注入器初始化成功"""
        mock_cdll.return_value = self.mock_lib

        injector = SeccompInjector(language="python")

        assert injector.language == "python"
        assert injector._lib == self.mock_lib

    @patch("src.security.injection.seccomp_wrapper.ctypes.CDLL")
    def test_injector_initialization_failure(self, mock_cdll):
        """测试注入器初始化失败"""
        mock_cdll.side_effect = OSError("Library not found")

        with pytest.raises(SeccompInjectionError) as exc_info:
            SeccompInjector(language="python")
        assert "Failed to load library" in str(exc_info.value)

    @patch("src.security.injection.seccomp_wrapper.ctypes.CDLL")
    def test_setup_no_new_privs_success(self, mock_cdll):
        """测试设置NO_NEW_PRIVS成功"""
        mock_cdll.return_value = self.mock_lib

        injector = SeccompInjector(language="python")
        injector.setup_no_new_privs()  # 应该不抛出异常

        self.mock_lib.setup_no_new_privs.assert_called_once()

    @patch("src.security.injection.seccomp_wrapper.ctypes.CDLL")
    def test_setup_no_new_privs_failure(self, mock_cdll):
        """测试设置NO_NEW_PRIVS失败"""
        self.mock_lib.setup_no_new_privs.return_value = -1  # 错误码
        mock_cdll.return_value = self.mock_lib

        injector = SeccompInjector(language="python")

        with pytest.raises(SeccompInjectionError):
            injector.setup_no_new_privs()

    @patch("src.security.injection.seccomp_wrapper.ctypes.CDLL")
    def test_drop_privileges_success(self, mock_cdll):
        """测试权限降级成功"""
        mock_cdll.return_value = self.mock_lib

        injector = SeccompInjector(language="python")
        injector.drop_privileges(1000, 1000)

        self.mock_lib.drop_privileges.assert_called_once_with(1000, 1000)

    @patch("src.security.injection.seccomp_wrapper.ctypes.CDLL")
    def test_apply_seccomp_filter_success(self, mock_cdll):
        """测试应用seccomp过滤器成功"""
        mock_cdll.return_value = self.mock_lib

        injector = SeccompInjector(language="python")
        injector.apply_seccomp_filter()

        self.mock_lib.apply_seccomp_filter.assert_called_once()

    @patch("src.security.injection.seccomp_wrapper.ctypes.CDLL")
    def test_inject_seccomp_profile_success(self, mock_cdll):
        """测试注入seccomp配置成功"""
        mock_cdll.return_value = self.mock_lib

        injector = SeccompInjector(language="python")
        injector.inject_seccomp_profile(1000, 1000)

        self.mock_lib.inject_seccomp_profile.assert_called_once_with(1000, 1000)

    @patch("src.security.injection.seccomp_wrapper.ctypes.CDLL")
    def test_get_error_description(self, mock_cdll):
        """测试获取错误描述"""
        self.mock_lib.get_error_description.return_value = b"Test error message"
        mock_cdll.return_value = self.mock_lib

        injector = SeccompInjector(language="python")
        desc = injector.get_error_description(0)

        assert desc == "Test error message"
        self.mock_lib.get_error_description.assert_called_once_with(0)

    def test_is_supported(self):
        """测试平台支持检查"""
        # 在Linux平台上应该返回True
        assert SeccompInjector.is_supported() is True


class TestSecurityPolicyIntegration:
    """安全策略集成测试"""

    @patch("src.security.SeccompInjector")
    def test_inject_seccomp_for_language_function(self, mock_injector_class):
        """测试便利函数inject_seccomp_for_language"""
        mock_injector = Mock()
        mock_injector_class.return_value = mock_injector

        inject_seccomp_for_language("python", 1000, 1000, "/path/to/lib")

        mock_injector_class.assert_called_once_with(
            library_path="/path/to/lib", language="python"
        )
        mock_injector.inject_seccomp_profile.assert_called_once_with(1000, 1000)

    @patch("src.security.SecurityManager")
    def test_create_secure_process_function(self, mock_manager_class):
        """测试便利函数create_secure_process"""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        create_secure_process("nodejs", 1000, 1000, "/path/to/lib")

        mock_manager_class.assert_called_once_with("/path/to/lib")
        mock_manager.setup_security_profile.assert_called_once_with(
            "nodejs", 1000, 1000
        )

    def test_security_error_handling(self):
        """测试安全错误处理"""
        with pytest.raises(SecurityError) as exc_info:
            raise SecurityError("Test security error")
        assert "Test security error" in str(exc_info.value)

    def test_seccomp_injection_error_handling(self):
        """测试seccomp注入错误处理"""
        with pytest.raises(SeccompInjectionError) as exc_info:
            raise SeccompInjectionError(-1, "Test injection error")
        assert "Test injection error" in str(exc_info.value)
        assert exc_info.value.error_code == -1


class TestSecurityWithRuntime:
    """安全与运行时集成测试"""

    @patch("src.security.SeccompInjector")
    def test_runtime_security_integration(self, mock_injector_class):
        """测试运行时与安全模块集成"""
        mock_injector = Mock()
        mock_injector_class.return_value = mock_injector

        security_manager = SecurityManager()

        # 模拟设置Python安全配置
        security_manager.setup_security_profile("python", 65534, 65534)

        # 验证注入器被正确调用
        mock_injector.inject_seccomp_profile.assert_called_once_with(
            65534, 65534
        )

    def test_security_config_files_exist(self):
        """测试安全配置文件存在"""
        python_config = (
            Path(__file__).parent.parent.parent
            / "src"
            / "security"
            / "static"
            / "python.json"
        )
        nodejs_config = (
            Path(__file__).parent.parent.parent
            / "src"
            / "security"
            / "static"
            / "nodejs.json"
        )

        assert python_config.exists()
        assert nodejs_config.exists()

    def test_security_config_content(self):
        """测试安全配置文件内容"""
        import json

        python_config = (
            Path(__file__).parent.parent.parent
            / "src"
            / "security"
            / "static"
            / "python.json"
        )
        with open(python_config, "r") as f:
            config = json.load(f)

        assert config["language"] == "python"
        assert "defaultAction" in config
        assert "syscalls" in config
        assert len(config["syscalls"]) > 0

    def test_runtime_with_security(self):
        """测试运行时与安全模块集成"""
        from src.runtime.python_runtime import PythonRuntime

        # 创建运行时
        runtime = PythonRuntime()

        # 验证运行时能正常创建和执行
        assert runtime is not None
        assert runtime.get_language() == "python"


class TestSecurityBoundaryConditions:
    """安全边界条件测试"""

    @patch("src.security.SeccompInjector")
    def test_error_code_handling(self, mock_injector_class):
        """测试错误码处理"""
        mock_injector = Mock()
        mock_injector_class.return_value = mock_injector

        # 测试各种错误码
        error_codes = [-1, -2, -3, -4, -5, -6]
        for error_code in error_codes:
            mock_injector.inject_seccomp_profile.side_effect = (
                SeccompInjectionError(error_code)
            )

            security_manager = SecurityManager()

            with pytest.raises(SeccompInjectionError) as exc_info:
                security_manager.setup_security_profile("python", 1000, 1000)

            assert exc_info.value.error_code == error_code

    def test_concurrent_security_operations(self):
        """测试并发安全操作"""
        import queue
        import threading

        results = queue.Queue()

        def setup_security():
            try:
                with patch(
                    "src.security.SeccompInjector"
                ) as mock_injector_class:
                    mock_injector = Mock()
                    mock_injector_class.return_value = mock_injector

                    security_manager = SecurityManager()
                    security_manager.setup_security_profile(
                        "python", 1000, 1000
                    )
                    results.put(True)
            except Exception:
                results.put(False)

        # 启动多个线程
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=setup_security)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 检查结果
        success_count = 0
        for _ in range(3):
            if results.get():
                success_count += 1

        assert success_count == 3
