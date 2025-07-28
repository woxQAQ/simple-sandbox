#!/usr/bin/env python3
"""
security模块集成测试

测试SecurityManager、SeccompInjector等核心组件的集成功能
"""

import os
import sys
import tempfile
import unittest.mock as mock
from pathlib import Path

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.security import (
        SECCOMP_ERROR_MEMORY,
        SECCOMP_ERROR_PRCTL,
        SECCOMP_ERROR_SYSCALL,
        SECCOMP_SUCCESS,
        SeccompInjectionError,
        SeccompInjector,
        SecurityError,
        SecurityManager,
        create_secure_process,
        get_default_security_manager,
        inject_seccomp_for_language,
    )
except ImportError as e:
    pytest.skip(f"Security module not available: {e}", allow_module_level=True)


class TestSecurityManager:
    """SecurityManager类的集成测试"""

    def setup_method(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SecurityManager(library_dir=self.temp_dir)

    def teardown_method(self):
        """测试后的清理"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_supported_languages(self):
        """测试支持的语言列表"""
        languages = self.manager.get_supported_languages()
        assert isinstance(languages, list)
        assert "python" in languages
        assert "nodejs" in languages
        assert len(languages) >= 2

    def test_seccomp_support_check(self):
        """测试seccomp支持检查"""
        # 在Linux系统上应该返回True
        if sys.platform.startswith("linux"):
            assert self.manager.is_seccomp_supported() is True
        else:
            # 在非Linux系统上可能抛出异常或返回False
            pass

    def test_unsupported_language(self):
        """测试不支持的语言"""
        with pytest.raises(SecurityError, match="Unsupported language"):
            self.manager._get_injector_for_language("unsupported_lang")

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_injector_caching(self):
        """测试注入器缓存机制"""
        # 模拟库文件存在
        with mock.patch.object(SeccompInjector, "__init__", return_value=None):
            with mock.patch.object(SeccompInjector, "_load_library"):
                injector1 = self.manager._get_injector_for_language("python")
                injector2 = self.manager._get_injector_for_language("python")
                # 应该返回同一个实例（缓存）
                assert injector1 is injector2

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_different_language_injectors(self):
        """测试不同语言的注入器是独立的"""
        with mock.patch.object(SeccompInjector, "__init__", return_value=None):
            with mock.patch.object(SeccompInjector, "_load_library"):
                python_injector = self.manager._get_injector_for_language(
                    "python"
                )
                nodejs_injector = self.manager._get_injector_for_language(
                    "nodejs"
                )
                # 应该是不同的实例
                assert python_injector is not nodejs_injector


class TestSeccompInjector:
    """SeccompInjector类的集成测试"""

    def setup_method(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """测试后的清理"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_library_path_construction(self):
        """测试库文件路径构建"""
        with mock.patch("ctypes.CDLL"):
            injector = SeccompInjector(
                language="python", library_path=self.temp_dir
            )
            expected_path = os.path.join(
                self.temp_dir, "libseccomp_injector_python.so"
            )
            assert injector.library_path == expected_path

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_library_loading_failure(self):
        """测试库文件加载失败"""
        with pytest.raises(
            SeccompInjectionError, match="Failed to load seccomp library"
        ):
            SeccompInjector(language="python", library_path="/nonexistent/path")

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_error_code_handling(self):
        """测试错误码处理"""
        with mock.patch("ctypes.CDLL"):
            injector = SeccompInjector(
                language="python", library_path=self.temp_dir
            )

            # 测试已知错误码
            assert "Success" in injector.get_error_description(SECCOMP_SUCCESS)
            assert "prctl" in injector.get_error_description(
                SECCOMP_ERROR_PRCTL
            )
            assert "seccomp" in injector.get_error_description(
                SECCOMP_ERROR_SYSCALL
            )

            # 测试未知错误码
            assert "Unknown" in injector.get_error_description(-999)

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_platform_support_check(self):
        """测试平台支持检查"""
        # 在Linux上应该支持
        assert SeccompInjector.is_supported() is True


class TestSecurityIntegration:
    """安全模块整体集成测试"""

    def setup_method(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """测试后的清理"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_security_profile_setup_workflow(self):
        """测试完整的安全配置设置流程"""
        manager = SecurityManager(library_dir=self.temp_dir)

        # 模拟成功的注入器
        mock_injector = mock.MagicMock()
        mock_injector.inject_seccomp_profile.return_value = None

        with mock.patch.object(
            manager, "_get_injector_for_language", return_value=mock_injector
        ):
            # 应该能够成功设置安全配置
            manager.setup_security_profile("python", 1000, 1000)

            # 验证注入器被正确调用
            mock_injector.inject_seccomp_profile.assert_called_once_with(
                1000, 1000
            )

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_privilege_operations(self):
        """测试权限相关操作"""
        manager = SecurityManager(library_dir=self.temp_dir)

        mock_injector = mock.MagicMock()

        with mock.patch.object(
            manager, "_get_injector_for_language", return_value=mock_injector
        ):
            # 测试设置no_new_privs
            manager.setup_no_new_privs("python")
            mock_injector.setup_no_new_privs.assert_called_once()

            # 测试降低权限
            manager.drop_privileges("python", 1000, 1000)
            mock_injector.drop_privileges.assert_called_once_with(1000, 1000)

            # 测试应用seccomp过滤器
            manager.apply_seccomp_filter("python")
            mock_injector.apply_seccomp_filter.assert_called_once()

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_convenience_functions(self):
        """测试便利函数"""
        with mock.patch("src.security.SecurityManager") as mock_manager_class:
            mock_manager = mock.MagicMock()
            mock_manager_class.return_value = mock_manager

            # 测试inject_seccomp_for_language
            inject_seccomp_for_language("python", 1000, 1000, self.temp_dir)
            mock_manager_class.assert_called_with(self.temp_dir)
            mock_manager.setup_security_profile.assert_called_with(
                "python", 1000, 1000
            )

            # 重置mock
            mock_manager_class.reset_mock()
            mock_manager.reset_mock()

            # 测试create_secure_process
            create_secure_process("nodejs", 2000, 2000, self.temp_dir)
            mock_manager_class.assert_called_with(self.temp_dir)
            mock_manager.setup_security_profile.assert_called_with(
                "nodejs", 2000, 2000
            )

    def test_default_security_manager(self):
        """测试默认安全管理器"""
        # 获取默认管理器
        manager1 = get_default_security_manager()
        manager2 = get_default_security_manager()

        # 应该返回同一个实例（单例模式）
        assert manager1 is manager2
        assert isinstance(manager1, SecurityManager)


class TestErrorHandling:
    """错误处理测试"""

    def test_security_error_creation(self):
        """测试SecurityError异常创建"""
        error = SecurityError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_seccomp_injection_error_creation(self):
        """测试SeccompInjectionError异常创建"""
        # 测试带错误码的异常
        error = SeccompInjectionError(SECCOMP_ERROR_PRCTL)
        assert "prctl" in str(error)
        assert error.error_code == SECCOMP_ERROR_PRCTL

        # 测试带自定义消息的异常
        error = SeccompInjectionError(SECCOMP_ERROR_MEMORY, "Custom message")
        assert "Custom message" in str(error)
        assert error.error_code == SECCOMP_ERROR_MEMORY


class TestConfigurationValidation:
    """配置验证测试"""

    def test_supported_languages_validation(self):
        """测试支持的语言验证"""
        manager = SecurityManager()

        # 测试有效语言
        for lang in ["python", "nodejs"]:
            try:
                # 这里可能会因为库文件不存在而失败，但不应该因为语言不支持而失败
                manager._get_injector_for_language(lang)
            except SecurityError as e:
                if "Unsupported language" in str(e):
                    pytest.fail(f"Language {lang} should be supported")
            except Exception:
                # 其他异常（如库文件不存在）是可以接受的
                pass

        # 测试无效语言
        with pytest.raises(SecurityError, match="Unsupported language"):
            manager._get_injector_for_language("invalid_language")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
