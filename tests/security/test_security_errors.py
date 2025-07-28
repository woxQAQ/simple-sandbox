#!/usr/bin/env python3
"""
安全模块错误处理和异常情况测试

测试SecurityError和SeccompInjectionError等异常类的行为
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
    from src.security import SecurityError, SecurityManager
    from src.security.injection.seccomp_wrapper import (
        ERROR_MESSAGES,
        SECCOMP_ERROR_INVALID_ARGS,
        SECCOMP_ERROR_MEMORY,
        SECCOMP_ERROR_PRCTL,
        SECCOMP_ERROR_PRIVILEGE,
        SECCOMP_ERROR_SYSCALL,
        SECCOMP_ERROR_UNSUPPORTED,
        SeccompInjectionError,
    )
except ImportError as e:
    pytest.skip(f"Security module not available: {e}", allow_module_level=True)


class TestSecurityError:
    """SecurityError异常类测试"""

    def test_security_error_creation(self):
        """测试SecurityError异常创建"""
        # 测试基本异常创建
        error = SecurityError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_security_error_inheritance(self):
        """测试SecurityError继承关系"""
        error = SecurityError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, SecurityError)

    def test_security_error_with_empty_message(self):
        """测试空消息的SecurityError"""
        error = SecurityError("")
        assert str(error) == ""

    def test_security_error_with_none_message(self):
        """测试None消息的SecurityError"""
        error = SecurityError(None)
        assert str(error) == "None"

    def test_security_error_with_complex_message(self):
        """测试复杂消息的SecurityError"""
        complex_message = "Security violation: unauthorized access to /etc/passwd with UID 1000"
        error = SecurityError(complex_message)
        assert str(error) == complex_message


class TestSeccompInjectionError:
    """SeccompInjectionError异常类测试"""

    def test_seccomp_injection_error_with_known_code(self):
        """测试已知错误码的SeccompInjectionError"""
        error = SeccompInjectionError(SECCOMP_ERROR_PRCTL)
        assert error.error_code == SECCOMP_ERROR_PRCTL
        assert "Seccomp injection failed" in str(error)
        assert ERROR_MESSAGES[SECCOMP_ERROR_PRCTL] in str(error)

    def test_seccomp_injection_error_with_unknown_code(self):
        """测试未知错误码的SeccompInjectionError"""
        unknown_code = -999
        error = SeccompInjectionError(unknown_code)
        assert error.error_code == unknown_code
        assert "Unknown error" in str(error)
        assert str(unknown_code) in str(error)

    def test_seccomp_injection_error_with_custom_message(self):
        """测试自定义消息的SeccompInjectionError"""
        custom_message = "Custom injection failure"
        error = SeccompInjectionError(SECCOMP_ERROR_MEMORY, custom_message)
        assert error.error_code == SECCOMP_ERROR_MEMORY
        assert error.message == custom_message
        assert custom_message in str(error)

    def test_seccomp_injection_error_inheritance(self):
        """测试SeccompInjectionError继承关系"""
        error = SeccompInjectionError(SECCOMP_ERROR_SYSCALL)
        assert isinstance(error, Exception)
        assert isinstance(error, SecurityError)
        assert isinstance(error, SeccompInjectionError)

    def test_all_error_codes_have_messages(self):
        """测试所有错误码都有对应的错误消息"""
        error_codes = [
            SECCOMP_ERROR_PRCTL,
            SECCOMP_ERROR_SYSCALL,
            SECCOMP_ERROR_INVALID_ARGS,
            SECCOMP_ERROR_PRIVILEGE,
            SECCOMP_ERROR_MEMORY,
            SECCOMP_ERROR_UNSUPPORTED,
        ]

        for code in error_codes:
            assert code in ERROR_MESSAGES
            assert isinstance(ERROR_MESSAGES[code], str)
            assert len(ERROR_MESSAGES[code]) > 0

            # 测试异常创建
            error = SeccompInjectionError(code)
            assert ERROR_MESSAGES[code] in str(error)

    def test_error_messages_content(self):
        """测试错误消息内容的合理性"""
        # 验证错误消息包含相关关键词
        expected_keywords = {
            SECCOMP_ERROR_PRCTL: ["prctl"],
            SECCOMP_ERROR_SYSCALL: ["syscall"],
            SECCOMP_ERROR_INVALID_ARGS: ["argument", "invalid"],
            SECCOMP_ERROR_PRIVILEGE: ["privilege", "permission"],
            SECCOMP_ERROR_MEMORY: ["memory"],
            SECCOMP_ERROR_UNSUPPORTED: ["unsupported", "support"],
        }

        for code, keywords in expected_keywords.items():
            message = ERROR_MESSAGES[code].lower()
            # 至少包含一个关键词
            assert any(
                keyword in message for keyword in keywords
            ), f"Error message for code {code} should contain one of {keywords}"


class TestSecurityManagerErrorHandling:
    """SecurityManager错误处理测试"""

    def setup_method(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """测试后的清理"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_unsupported_language_error(self):
        """测试不支持的语言错误"""
        manager = SecurityManager(library_dir=self.temp_dir)

        with pytest.raises(SecurityError, match="Unsupported language"):
            manager._get_injector_for_language("unsupported_language")

    def test_invalid_language_type_error(self):
        """测试无效语言类型错误"""
        manager = SecurityManager(library_dir=self.temp_dir)

        invalid_languages = [None, 123, [], {}, object()]
        for invalid_lang in invalid_languages:
            with pytest.raises((SecurityError, TypeError)):
                manager._get_injector_for_language(invalid_lang)

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_library_loading_error_propagation(self):
        """测试库加载错误传播"""
        manager = SecurityManager(library_dir="/nonexistent/directory")

        with pytest.raises(SecurityError):
            manager._get_injector_for_language("python")

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_seccomp_operation_error_propagation(self):
        """测试seccomp操作错误传播"""
        with mock.patch("src.security.SeccompInjector") as mock_injector_class:
            mock_injector = mock.MagicMock()
            mock_injector.inject_seccomp_profile.side_effect = (
                SeccompInjectionError(SECCOMP_ERROR_PRCTL)
            )
            mock_injector_class.return_value = mock_injector

            manager = SecurityManager(library_dir=self.temp_dir)

            with pytest.raises(SeccompInjectionError):
                manager.setup_security_profile("python", 1000, 1000)

    def test_invalid_uid_gid_values(self):
        """测试无效的UID/GID值"""
        manager = SecurityManager(library_dir=self.temp_dir)

        invalid_values = [
            (-1, 1000),  # 负数UID
            (1000, -1),  # 负数GID
            (-1, -1),  # 都是负数
            ("1000", 1000),  # 字符串UID
            (1000, "1000"),  # 字符串GID
            (None, 1000),  # None UID
            (1000, None),  # None GID
        ]

        for uid, gid in invalid_values:
            with pytest.raises((SecurityError, TypeError, ValueError)):
                manager.setup_security_profile("python", uid, gid)


class TestErrorRecoveryAndCleanup:
    """错误恢复和清理测试"""

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
    def test_partial_operation_failure_cleanup(self):
        """测试部分操作失败后的清理"""
        with mock.patch("src.security.SeccompInjector") as mock_injector_class:
            mock_injector = mock.MagicMock()
            # 模拟第一个操作成功，第二个操作失败
            mock_injector.setup_no_new_privs.return_value = None
            mock_injector.drop_privileges.side_effect = SeccompInjectionError(
                SECCOMP_ERROR_PRIVILEGE
            )
            mock_injector_class.return_value = mock_injector

            manager = SecurityManager(library_dir=self.temp_dir)

            with pytest.raises(SeccompInjectionError):
                manager.setup_security_profile("python", 1000, 1000)

            # 验证第一个操作被调用了
            mock_injector.setup_no_new_privs.assert_called_once()
            # 验证第二个操作也被尝试了
            mock_injector.drop_privileges.assert_called_once_with(1000, 1000)

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_multiple_error_scenarios(self):
        """测试多种错误场景"""
        error_scenarios = [
            (SECCOMP_ERROR_PRCTL, "prctl"),
            (SECCOMP_ERROR_SYSCALL, "syscall"),
            (SECCOMP_ERROR_MEMORY, "memory"),
            (SECCOMP_ERROR_PRIVILEGE, "privilege"),
        ]

        for error_code, expected_keyword in error_scenarios:
            with mock.patch(
                "src.security.SeccompInjector"
            ) as mock_injector_class:
                mock_injector = mock.MagicMock()
                mock_injector.apply_seccomp_filter.side_effect = (
                    SeccompInjectionError(error_code)
                )
                mock_injector_class.return_value = mock_injector

                manager = SecurityManager(library_dir=self.temp_dir)

                with pytest.raises(SeccompInjectionError) as exc_info:
                    manager.apply_seccomp_filter("python")

                # 验证错误消息包含预期关键词
                assert expected_keyword.lower() in str(exc_info.value).lower()


class TestErrorMessageLocalization:
    """错误消息本地化测试"""

    def test_error_messages_are_descriptive(self):
        """测试错误消息是否具有描述性"""
        for error_code, message in ERROR_MESSAGES.items():
            # 错误消息应该足够长，具有描述性
            assert (
                len(message) > 10
            ), f"Error message for {error_code} is too short"

            # 错误消息应该包含有用信息
            assert (
                not message.isspace()
            ), f"Error message for {error_code} is only whitespace"

            # 错误消息应该是字符串
            assert isinstance(
                message, str
            ), f"Error message for {error_code} is not a string"

    def test_error_messages_consistency(self):
        """测试错误消息的一致性"""
        # 所有错误消息都应该以大写字母开头
        for error_code, message in ERROR_MESSAGES.items():
            assert message[
                0
            ].isupper(), (
                f"Error message for {error_code} should start with uppercase"
            )

    def test_security_error_formatting(self):
        """测试SecurityError格式化"""
        test_messages = [
            "Simple error",
            "Error with numbers: 123",
            "Error with special chars: !@#$%",
            "Multi-line\nerror\nmessage",
            "Unicode error: 测试错误消息",
        ]

        for message in test_messages:
            error = SecurityError(message)
            assert str(error) == message

    def test_seccomp_injection_error_formatting(self):
        """测试SeccompInjectionError格式化"""
        # 测试不同错误码的格式化
        for error_code in ERROR_MESSAGES.keys():
            error = SeccompInjectionError(error_code)
            error_str = str(error)

            # 应该包含基本信息
            assert "Seccomp injection failed" in error_str
            assert str(error_code) in error_str
            assert ERROR_MESSAGES[error_code] in error_str


class TestExceptionChaining:
    """异常链测试"""

    def test_exception_chaining_with_cause(self):
        """测试带原因的异常链"""
        original_error = ValueError("Original error")

        try:
            raise original_error
        except ValueError as e:
            security_error = SecurityError("Security error occurred")
            security_error.__cause__ = e

            assert security_error.__cause__ is original_error
            assert str(security_error.__cause__) == "Original error"

    def test_exception_chaining_with_context(self):
        """测试带上下文的异常链"""
        try:
            try:
                raise ValueError("Original error")
            except ValueError:
                raise SecurityError("Security error occurred")
        except SecurityError as e:
            assert isinstance(e.__context__, ValueError)
            assert str(e.__context__) == "Original error"

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_seccomp_error_chaining(self):
        """测试SeccompInjectionError异常链"""
        with mock.patch("ctypes.CDLL") as mock_cdll:
            # 模拟ctypes.CDLL抛出异常
            mock_cdll.side_effect = OSError("Library not found")

            try:
                from src.security.injection.seccomp_wrapper import (
                    SeccompInjector,
                )

                SeccompInjector(library_path="/nonexistent/path.so")
            except SeccompInjectionError as e:
                # 应该有原始异常作为上下文或原因
                assert e.__context__ is not None or e.__cause__ is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
