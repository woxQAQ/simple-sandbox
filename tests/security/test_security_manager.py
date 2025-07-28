#!/usr/bin/env python3
"""
SecurityManager类的单元测试

专门测试SecurityManager类的各种功能和边界情况
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

try:
    from src.security import (
        SecurityManager,
        SecurityError,
        SeccompInjector,
    )
except ImportError as e:
    pytest.skip(f"Security module not available: {e}", allow_module_level=True)


class TestSecurityManagerInitialization:
    """SecurityManager初始化测试"""

    def test_default_initialization(self):
        """测试默认初始化"""
        manager = SecurityManager()
        assert manager.library_dir is None
        assert manager._injectors == {}
        assert manager.SUPPORTED_LANGUAGES == ["python", "nodejs"]

    def test_custom_library_dir_initialization(self, temp_directory):
        """测试自定义库目录初始化"""
        manager = SecurityManager(library_dir=temp_directory)
        assert manager.library_dir == temp_directory
        assert manager._injectors == {}

    def test_supported_languages_immutable(self):
        """测试支持的语言列表不可变"""
        manager = SecurityManager()
        languages1 = manager.get_supported_languages()
        languages2 = manager.get_supported_languages()

        # 应该返回不同的列表实例（副本）
        assert languages1 is not languages2
        assert languages1 == languages2

        # 修改返回的列表不应该影响原始列表
        languages1.append("test_language")
        languages3 = manager.get_supported_languages()
        assert "test_language" not in languages3


class TestSecurityManagerLanguageSupport:
    """SecurityManager语言支持测试"""

    def setup_method(self):
        """测试前的设置"""
        self.manager = SecurityManager()

    def test_supported_languages_list(self):
        """测试支持的语言列表"""
        languages = self.manager.get_supported_languages()
        assert isinstance(languages, list)
        assert len(languages) >= 2
        assert "python" in languages
        assert "nodejs" in languages

    def test_unsupported_language_error(self):
        """测试不支持的语言错误"""
        unsupported_languages = [
            "java",
            "cpp",
            "rust",
            "go",
            "php",
            "ruby",
            "invalid",
            "",
            "123",
            "python3",
            "node",
        ]

        for lang in unsupported_languages:
            with pytest.raises(SecurityError, match="Unsupported language"):
                self.manager._get_injector_for_language(lang)

    def test_case_sensitive_language_check(self):
        """测试语言名称大小写敏感"""
        case_variants = [
            "Python",
            "PYTHON",
            "PyThOn",
            "NodeJS",
            "NODEJS",
            "NodeJs",
        ]

        for lang in case_variants:
            with pytest.raises(SecurityError, match="Unsupported language"):
                self.manager._get_injector_for_language(lang)


class TestSecurityManagerInjectorManagement:
    """SecurityManager注入器管理测试"""

    def setup_method(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SecurityManager(library_dir=self.temp_dir)

    def teardown_method(self):
        """测试后的清理"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_injector_caching(self):
        """测试注入器缓存机制"""
        with mock.patch.object(SeccompInjector, "__init__", return_value=None):
            with mock.patch.object(SeccompInjector, "_load_library"):
                # 第一次获取
                injector1 = self.manager._get_injector_for_language("python")
                assert "python" in self.manager._injectors

                # 第二次获取应该返回缓存的实例
                injector2 = self.manager._get_injector_for_language("python")
                assert injector1 is injector2

                # 验证SeccompInjector只被初始化一次
                assert SeccompInjector.__init__.call_count == 1

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

                # 两个语言都应该在缓存中
                assert "python" in self.manager._injectors
                assert "nodejs" in self.manager._injectors
                assert len(self.manager._injectors) == 2

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_injector_creation_failure(self):
        """测试注入器创建失败"""
        with mock.patch.object(
            SeccompInjector, "__init__", side_effect=Exception("Mock error")
        ):
            with pytest.raises(
                SecurityError,
                match="Failed to load seccomp injector for python",
            ):
                self.manager._get_injector_for_language("python")

            # 失败的注入器不应该被缓存
            assert "python" not in self.manager._injectors

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_injector_library_path_passing(self):
        """测试注入器库路径传递"""
        with mock.patch.object(
            SeccompInjector, "__init__", return_value=None
        ) as mock_init:
            with mock.patch.object(SeccompInjector, "_load_library"):
                self.manager._get_injector_for_language("python")

                # 验证SeccompInjector被正确初始化
                mock_init.assert_called_once_with("python", self.temp_dir)


class TestSecurityManagerOperations:
    """SecurityManager操作测试"""

    def setup_method(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SecurityManager(library_dir=self.temp_dir)
        self.mock_injector = mock.MagicMock()

    def teardown_method(self):
        """测试后的清理"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_setup_security_profile(self):
        """测试安全配置设置"""
        with mock.patch.object(
            self.manager,
            "_get_injector_for_language",
            return_value=self.mock_injector,
        ):
            self.manager.setup_security_profile("python", 1000, 1000)

            # 验证注入器方法被调用
            self.mock_injector.inject_seccomp_profile.assert_called_once_with(
                1000, 1000
            )

    def test_setup_no_new_privs(self):
        """测试设置no_new_privs"""
        with mock.patch.object(
            self.manager,
            "_get_injector_for_language",
            return_value=self.mock_injector,
        ):
            self.manager.setup_no_new_privs("python")

            self.mock_injector.setup_no_new_privs.assert_called_once()

    def test_drop_privileges(self):
        """测试降低权限"""
        with mock.patch.object(
            self.manager,
            "_get_injector_for_language",
            return_value=self.mock_injector,
        ):
            self.manager.drop_privileges("python", 2000, 2000)

            self.mock_injector.drop_privileges.assert_called_once_with(
                2000, 2000
            )

    def test_apply_seccomp_filter(self):
        """测试应用seccomp过滤器"""
        with mock.patch.object(
            self.manager,
            "_get_injector_for_language",
            return_value=self.mock_injector,
        ):
            self.manager.apply_seccomp_filter("nodejs")

            self.mock_injector.apply_seccomp_filter.assert_called_once()

    def test_operations_with_invalid_language(self):
        """测试使用无效语言进行操作"""
        operations = [
            ("setup_security_profile", ["invalid_lang", 1000, 1000]),
            ("setup_no_new_privs", ["invalid_lang"]),
            ("drop_privileges", ["invalid_lang", 1000, 1000]),
            ("apply_seccomp_filter", ["invalid_lang"]),
        ]

        for op_name, args in operations:
            with pytest.raises(SecurityError, match="Unsupported language"):
                getattr(self.manager, op_name)(*args)

    def test_operations_with_injector_failure(self):
        """测试注入器操作失败"""
        # 模拟注入器操作失败
        self.mock_injector.inject_seccomp_profile.side_effect = Exception(
            "Injection failed"
        )

        with mock.patch.object(
            self.manager,
            "_get_injector_for_language",
            return_value=self.mock_injector,
        ):
            with pytest.raises(Exception, match="Injection failed"):
                self.manager.setup_security_profile("python", 1000, 1000)


class TestSecurityManagerEdgeCases:
    """SecurityManager边界情况测试"""

    def test_is_seccomp_supported(self):
        """测试seccomp支持检查"""
        manager = SecurityManager()
        # 目前总是返回True（因为模块只在Linux上可用）
        assert manager.is_seccomp_supported() is True

    def test_multiple_managers_independence(self):
        """测试多个管理器实例的独立性"""
        manager1 = SecurityManager(library_dir="/path1")
        manager2 = SecurityManager(library_dir="/path2")

        assert manager1.library_dir != manager2.library_dir
        assert manager1._injectors is not manager2._injectors

        # 修改一个管理器不应该影响另一个
        manager1._injectors["test"] = "value"
        assert "test" not in manager2._injectors

    def test_extreme_uid_gid_values(self):
        """测试极端的UID/GID值"""
        manager = SecurityManager()
        mock_injector = mock.MagicMock()

        extreme_values = [
            (0, 0),  # root
            (65534, 65534),  # nobody
            (999999, 999999),  # 大值
        ]

        with mock.patch.object(
            manager, "_get_injector_for_language", return_value=mock_injector
        ):
            for uid, gid in extreme_values:
                manager.setup_security_profile("python", uid, gid)
                mock_injector.inject_seccomp_profile.assert_called_with(
                    uid, gid
                )
                mock_injector.reset_mock()

    def test_concurrent_access_simulation(self):
        """测试并发访问模拟"""
        manager = SecurityManager()

        # 模拟多个"线程"同时访问同一个语言的注入器
        with mock.patch.object(SeccompInjector, "__init__", return_value=None):
            with mock.patch.object(SeccompInjector, "_load_library"):
                injectors = []
                for _ in range(5):
                    injector = manager._get_injector_for_language("python")
                    injectors.append(injector)

                # 所有注入器应该是同一个实例
                for injector in injectors[1:]:
                    assert injector is injectors[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
