#!/usr/bin/env python3
"""
SeccompInjector类的单元测试

专门测试SeccompInjector类的各种功能和边界情况
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
    from src.security.injection.seccomp_wrapper import (
        ERROR_MESSAGES,
        SECCOMP_ERROR_MEMORY,
        SECCOMP_ERROR_PRCTL,
        SECCOMP_ERROR_PRIVILEGE,
        SECCOMP_ERROR_SYSCALL,
        SECCOMP_SUCCESS,
        SeccompInjectionError,
        SeccompInjector,
        inject_seccomp_for_language,
    )
except ImportError as e:
    pytest.skip(
        f"SeccompInjector module not available: {e}", allow_module_level=True
    )


class TestSeccompInjectorInitialization:
    """SeccompInjector初始化测试"""

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
    def test_initialization_with_language_and_path(self):
        """测试使用语言和路径初始化"""
        with mock.patch("ctypes.CDLL") as mock_cdll:
            injector = SeccompInjector(
                language="python", library_path=self.temp_dir
            )

            expected_path = os.path.join(
                self.temp_dir, "libseccomp_injector_python.so"
            )
            assert injector.library_path == expected_path
            assert injector.language == "python"
            mock_cdll.assert_called_once_with(expected_path)

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_initialization_with_only_language(self):
        """测试仅使用语言初始化"""
        with mock.patch("ctypes.CDLL") as mock_cdll:
            with mock.patch.object(
                SeccompInjector,
                "_find_library_path",
                return_value="/mock/path.so",
            ):
                injector = SeccompInjector(language="nodejs")

                assert injector.language == "nodejs"
                assert injector.library_path == "/mock/path.so"
                mock_cdll.assert_called_once_with("/mock/path.so")

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_initialization_with_only_path(self):
        """测试仅使用路径初始化"""
        library_path = os.path.join(self.temp_dir, "libseccomp_injector.so")

        with mock.patch("ctypes.CDLL") as mock_cdll:
            injector = SeccompInjector(library_path=library_path)

            assert injector.library_path == library_path
            assert injector.language is None
            mock_cdll.assert_called_once_with(library_path)

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_initialization_without_parameters(self):
        """测试无参数初始化"""
        with mock.patch("ctypes.CDLL") as mock_cdll:
            with mock.patch.object(
                SeccompInjector,
                "_find_library_path",
                return_value="/default/path.so",
            ):
                injector = SeccompInjector()

                assert injector.language is None
                assert injector.library_path == "/default/path.so"
                mock_cdll.assert_called_once_with("/default/path.so")

    def test_library_loading_failure(self):
        """测试库文件加载失败"""
        with pytest.raises(
            SeccompInjectionError, match="Failed to load seccomp library"
        ):
            SeccompInjector(library_path="/nonexistent/path/libseccomp.so")


class TestSeccompInjectorLibraryPathFinding:
    """SeccompInjector库路径查找测试"""

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
    def test_find_library_path_with_language(self):
        """测试根据语言查找库路径"""
        with mock.patch("ctypes.CDLL"):
            injector = SeccompInjector.__new__(SeccompInjector)

            # 测试不同语言的路径构建
            languages = ["python", "nodejs", "java", "cpp"]
            for lang in languages:
                path = injector._find_library_path(lang)
                assert f"libseccomp_injector_{lang}.so" in path
                assert path.endswith(".so")

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_find_library_path_without_language(self):
        """测试不指定语言时查找库路径"""
        with mock.patch("ctypes.CDLL"):
            injector = SeccompInjector.__new__(SeccompInjector)

            path = injector._find_library_path()
            assert "libseccomp_injector.so" in path
            assert path.endswith(".so")

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_find_library_path_relative_to_module(self):
        """测试相对于模块的库路径查找"""
        with mock.patch("ctypes.CDLL"):
            injector = SeccompInjector.__new__(SeccompInjector)

            path = injector._find_library_path("python")
            # 路径应该包含bpf目录
            assert "bpf" in path
            # 路径应该是绝对路径
            assert os.path.isabs(path)


class TestSeccompInjectorFunctionSignatures:
    """SeccompInjector函数签名测试"""

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_function_signatures_setup(self):
        """测试函数签名设置"""
        with mock.patch("ctypes.CDLL") as mock_cdll:
            mock_lib = mock.MagicMock()
            mock_cdll.return_value = mock_lib

            SeccompInjector(language="python", library_path="/mock/path.so")

            # 验证函数签名被设置
            assert hasattr(mock_lib.inject_seccomp_profile, "argtypes")
            assert hasattr(mock_lib.inject_seccomp_profile, "restype")
            assert hasattr(mock_lib.setup_no_new_privs, "argtypes")
            assert hasattr(mock_lib.setup_no_new_privs, "restype")
            assert hasattr(mock_lib.drop_privileges, "argtypes")
            assert hasattr(mock_lib.drop_privileges, "restype")
            assert hasattr(mock_lib.apply_seccomp_filter, "argtypes")
            assert hasattr(mock_lib.apply_seccomp_filter, "restype")


class TestSeccompInjectorOperations:
    """SeccompInjector操作测试"""

    def setup_method(self):
        """测试前的设置"""
        self.mock_lib = mock.MagicMock()

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_inject_seccomp_profile_success(self):
        """测试成功注入seccomp配置"""
        with mock.patch("ctypes.CDLL", return_value=self.mock_lib):
            self.mock_lib.inject_seccomp_profile.return_value = SECCOMP_SUCCESS

            injector = SeccompInjector(
                language="python", library_path="/mock/path.so"
            )

            # 应该成功执行，不抛出异常
            injector.inject_seccomp_profile(1000, 1000)

            self.mock_lib.inject_seccomp_profile.assert_called_once_with(
                1000, 1000
            )

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_inject_seccomp_profile_failure(self):
        """测试注入seccomp配置失败"""
        with mock.patch("ctypes.CDLL", return_value=self.mock_lib):
            self.mock_lib.inject_seccomp_profile.return_value = (
                SECCOMP_ERROR_PRCTL
            )

            injector = SeccompInjector(
                language="python", library_path="/mock/path.so"
            )

            with pytest.raises(
                SeccompInjectionError, match="Failed to inject seccomp profile"
            ):
                injector.inject_seccomp_profile(1000, 1000)

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_setup_no_new_privs_success(self):
        """测试成功设置no_new_privs"""
        with mock.patch("ctypes.CDLL", return_value=self.mock_lib):
            self.mock_lib.setup_no_new_privs.return_value = SECCOMP_SUCCESS

            injector = SeccompInjector(
                language="python", library_path="/mock/path.so"
            )

            injector.setup_no_new_privs()

            self.mock_lib.setup_no_new_privs.assert_called_once()

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_setup_no_new_privs_failure(self):
        """测试设置no_new_privs失败"""
        with mock.patch("ctypes.CDLL", return_value=self.mock_lib):
            self.mock_lib.setup_no_new_privs.return_value = SECCOMP_ERROR_PRCTL

            injector = SeccompInjector(
                language="python", library_path="/mock/path.so"
            )

            with pytest.raises(
                SeccompInjectionError, match="Failed to setup no new privs"
            ):
                injector.setup_no_new_privs()

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_drop_privileges_success(self):
        """测试成功降低权限"""
        with mock.patch("ctypes.CDLL", return_value=self.mock_lib):
            self.mock_lib.drop_privileges.return_value = SECCOMP_SUCCESS

            injector = SeccompInjector(
                language="python", library_path="/mock/path.so"
            )

            injector.drop_privileges(2000, 2000)

            self.mock_lib.drop_privileges.assert_called_once_with(2000, 2000)

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_drop_privileges_failure(self):
        """测试降低权限失败"""
        with mock.patch("ctypes.CDLL", return_value=self.mock_lib):
            self.mock_lib.drop_privileges.return_value = SECCOMP_ERROR_PRIVILEGE

            injector = SeccompInjector(
                language="python", library_path="/mock/path.so"
            )

            with pytest.raises(
                SeccompInjectionError, match="Failed to drop privileges"
            ):
                injector.drop_privileges(2000, 2000)

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_apply_seccomp_filter_success(self):
        """测试成功应用seccomp过滤器"""
        with mock.patch("ctypes.CDLL", return_value=self.mock_lib):
            self.mock_lib.apply_seccomp_filter.return_value = SECCOMP_SUCCESS

            injector = SeccompInjector(
                language="python", library_path="/mock/path.so"
            )

            injector.apply_seccomp_filter()

            self.mock_lib.apply_seccomp_filter.assert_called_once()

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_apply_seccomp_filter_failure(self):
        """测试应用seccomp过滤器失败"""
        with mock.patch("ctypes.CDLL", return_value=self.mock_lib):
            self.mock_lib.apply_seccomp_filter.return_value = (
                SECCOMP_ERROR_SYSCALL
            )

            injector = SeccompInjector(
                language="python", library_path="/mock/path.so"
            )

            with pytest.raises(
                SeccompInjectionError, match="Failed to apply seccomp filter"
            ):
                injector.apply_seccomp_filter()


class TestSeccompInjectorErrorHandling:
    """SeccompInjector错误处理测试"""

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_error_description_known_codes(self):
        """测试已知错误码的描述"""
        with mock.patch("ctypes.CDLL"):
            injector = SeccompInjector(
                language="python", library_path="/mock/path.so"
            )

            # 测试所有已知错误码
            for error_code, expected_message in ERROR_MESSAGES.items():
                description = injector.get_error_description(error_code)
                assert expected_message in description

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_error_description_unknown_codes(self):
        """测试未知错误码的描述"""
        with mock.patch("ctypes.CDLL"):
            injector = SeccompInjector(
                language="python", library_path="/mock/path.so"
            )

            unknown_codes = [-999, -100, 999, 100]
            for error_code in unknown_codes:
                description = injector.get_error_description(error_code)
                assert "Unknown error" in description

    def test_seccomp_injection_error_creation(self):
        """测试SeccompInjectionError异常创建"""
        # 测试带错误码的异常
        error = SeccompInjectionError(SECCOMP_ERROR_PRCTL)
        assert error.error_code == SECCOMP_ERROR_PRCTL
        assert "prctl" in str(error)
        assert "Seccomp injection failed" in str(error)

        # 测试带自定义消息的异常
        custom_message = "Custom error message"
        error = SeccompInjectionError(SECCOMP_ERROR_MEMORY, custom_message)
        assert error.error_code == SECCOMP_ERROR_MEMORY
        assert custom_message in str(error)
        assert error.message == custom_message

        # 测试未知错误码
        error = SeccompInjectionError(-999)
        assert error.error_code == -999
        assert "Unknown error" in str(error)


class TestSeccompInjectorStaticMethods:
    """SeccompInjector静态方法测试"""

    def test_is_supported_on_linux(self):
        """测试Linux平台支持检查"""
        if sys.platform.startswith("linux"):
            assert SeccompInjector.is_supported() is True
        else:
            # 在非Linux平台上，模块应该无法导入
            # 如果能导入，说明测试环境有问题
            pass


class TestSeccompInjectorConvenienceFunction:
    """SeccompInjector便利函数测试"""

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_inject_seccomp_for_language_function(self):
        """测试便利函数inject_seccomp_for_language"""
        with mock.patch(
            "src.security.injection.seccomp_wrapper.SeccompInjector"
        ) as mock_injector_class:
            mock_injector = mock.MagicMock()
            mock_injector_class.return_value = mock_injector

            inject_seccomp_for_language("python", 1000, 1000, "/mock/path")

            # 验证SeccompInjector被正确创建
            mock_injector_class.assert_called_once_with(
                language="python", library_path="/mock/path"
            )

            # 验证inject_seccomp_profile被调用
            mock_injector.inject_seccomp_profile.assert_called_once_with(
                1000, 1000
            )

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_inject_seccomp_for_language_function_without_path(self):
        """测试便利函数不指定路径"""
        with mock.patch(
            "src.security.injection.seccomp_wrapper.SeccompInjector"
        ) as mock_injector_class:
            mock_injector = mock.MagicMock()
            mock_injector_class.return_value = mock_injector

            inject_seccomp_for_language("nodejs", 2000, 2000)

            # 验证SeccompInjector被正确创建（不传递library_path）
            mock_injector_class.assert_called_once_with(
                language="nodejs", library_path=None
            )

            # 验证inject_seccomp_profile被调用
            mock_injector.inject_seccomp_profile.assert_called_once_with(
                2000, 2000
            )


class TestSeccompInjectorEdgeCases:
    """SeccompInjector边界情况测试"""

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_extreme_uid_gid_values(self):
        """测试极端UID/GID值"""
        with mock.patch("ctypes.CDLL") as mock_cdll:
            mock_lib = mock.MagicMock()
            mock_lib.inject_seccomp_profile.return_value = SECCOMP_SUCCESS
            mock_lib.drop_privileges.return_value = SECCOMP_SUCCESS
            mock_cdll.return_value = mock_lib

            injector = SeccompInjector(
                language="python", library_path="/mock/path.so"
            )

            extreme_values = [
                (0, 0),  # root
                (65534, 65534),  # nobody
                (4294967295, 4294967295),  # 最大32位无符号整数
            ]

            for uid, gid in extreme_values:
                injector.inject_seccomp_profile(uid, gid)
                injector.drop_privileges(uid, gid)

                mock_lib.inject_seccomp_profile.assert_called_with(uid, gid)
                mock_lib.drop_privileges.assert_called_with(uid, gid)

                mock_lib.reset_mock()

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_multiple_operations_sequence(self):
        """测试多个操作的序列"""
        with mock.patch("ctypes.CDLL") as mock_cdll:
            mock_lib = mock.MagicMock()
            mock_lib.setup_no_new_privs.return_value = SECCOMP_SUCCESS
            mock_lib.drop_privileges.return_value = SECCOMP_SUCCESS
            mock_lib.apply_seccomp_filter.return_value = SECCOMP_SUCCESS
            mock_lib.inject_seccomp_profile.return_value = SECCOMP_SUCCESS
            mock_cdll.return_value = mock_lib

            injector = SeccompInjector(
                language="python", library_path="/mock/path.so"
            )

            # 执行一系列操作
            injector.setup_no_new_privs()
            injector.drop_privileges(1000, 1000)
            injector.apply_seccomp_filter()
            injector.inject_seccomp_profile(1000, 1000)

            # 验证所有操作都被调用
            mock_lib.setup_no_new_privs.assert_called_once()
            mock_lib.drop_privileges.assert_called_once_with(1000, 1000)
            mock_lib.apply_seccomp_filter.assert_called_once()
            mock_lib.inject_seccomp_profile.assert_called_once_with(1000, 1000)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
