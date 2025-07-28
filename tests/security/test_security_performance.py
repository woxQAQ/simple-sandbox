#!/usr/bin/env python3
"""
安全模块性能和压力测试

测试SecurityManager和SeccompInjector在高负载和边界条件下的性能表现
"""

import os
import sys
import time
import pytest
import tempfile
import threading
import concurrent.futures
import unittest.mock as mock
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.security import SecurityManager, SecurityError
    from src.security.injection.seccomp_wrapper import (
        SeccompInjector,
        SeccompInjectionError,
        SECCOMP_SUCCESS,
    )
except ImportError as e:
    pytest.skip(f"Security module not available: {e}", allow_module_level=True)


class TestSecurityManagerPerformance:
    """SecurityManager性能测试"""

    def setup_method(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SecurityManager(library_dir=self.temp_dir)

    def teardown_method(self):
        """测试后的清理"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_injector_caching_performance(self):
        """测试注入器缓存性能"""
        with mock.patch("src.security.SeccompInjector") as mock_injector_class:
            mock_injector = mock.MagicMock()
            mock_injector_class.return_value = mock_injector

            # 第一次获取注入器
            start_time = time.time()
            injector1 = self.manager._get_injector_for_language("python")
            first_call_time = time.time() - start_time

            # 第二次获取相同语言的注入器（应该从缓存获取）
            start_time = time.time()
            injector2 = self.manager._get_injector_for_language("python")
            second_call_time = time.time() - start_time

            # 验证返回的是同一个实例
            assert injector1 is injector2

            # 第二次调用应该明显更快（缓存效果）
            assert second_call_time < first_call_time * 0.5

            # SeccompInjector构造函数应该只被调用一次
            assert mock_injector_class.call_count == 1

    def test_multiple_language_injector_performance(self):
        """测试多语言注入器性能"""
        languages = ["python", "nodejs", "java", "cpp"]

        with mock.patch("src.security.SeccompInjector") as mock_injector_class:
            mock_injector_class.return_value = mock.MagicMock()

            start_time = time.time()

            # 为每种语言获取注入器
            injectors = {}
            for lang in languages:
                injectors[lang] = self.manager._get_injector_for_language(lang)

            total_time = time.time() - start_time

            # 验证每种语言都有独立的注入器
            assert len(set(injectors.values())) == len(languages)

            # 验证总时间合理（不应该过长）
            assert total_time < 1.0  # 1秒内完成

            # 验证每种语言的构造函数都被调用
            assert mock_injector_class.call_count == len(languages)

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_rapid_security_profile_setup(self):
        """测试快速安全配置设置"""
        with mock.patch("src.security.SeccompInjector") as mock_injector_class:
            mock_injector = mock.MagicMock()
            mock_injector.setup_no_new_privs.return_value = None
            mock_injector.drop_privileges.return_value = None
            mock_injector.apply_seccomp_filter.return_value = None
            mock_injector_class.return_value = mock_injector

            # 测试快速连续设置安全配置
            iterations = 100
            start_time = time.time()

            for i in range(iterations):
                self.manager.setup_security_profile(
                    "python", 1000 + i, 1000 + i
                )

            total_time = time.time() - start_time
            avg_time_per_call = total_time / iterations

            # 平均每次调用应该很快
            assert avg_time_per_call < 0.01  # 10ms内

            # 验证所有调用都执行了
            assert mock_injector.setup_no_new_privs.call_count == iterations
            assert mock_injector.drop_privileges.call_count == iterations
            assert mock_injector.apply_seccomp_filter.call_count == iterations


class TestSeccompInjectorPerformance:
    """SeccompInjector性能测试"""

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_library_loading_performance(self):
        """测试库加载性能"""
        with mock.patch("ctypes.CDLL") as mock_cdll:
            mock_lib = mock.MagicMock()
            mock_cdll.return_value = mock_lib

            # 测试多次创建SeccompInjector的性能
            iterations = 50
            start_time = time.time()

            injectors = []
            for i in range(iterations):
                injector = SeccompInjector(
                    language="python", library_path=f"/mock/path_{i}.so"
                )
                injectors.append(injector)

            total_time = time.time() - start_time
            avg_time_per_creation = total_time / iterations

            # 平均每次创建应该很快
            assert avg_time_per_creation < 0.02  # 20ms内

            # 验证所有实例都创建成功
            assert len(injectors) == iterations
            assert mock_cdll.call_count == iterations

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_rapid_seccomp_operations(self):
        """测试快速seccomp操作"""
        with mock.patch("ctypes.CDLL") as mock_cdll:
            mock_lib = mock.MagicMock()
            mock_lib.inject_seccomp_profile.return_value = SECCOMP_SUCCESS
            mock_lib.setup_no_new_privs.return_value = SECCOMP_SUCCESS
            mock_lib.drop_privileges.return_value = SECCOMP_SUCCESS
            mock_lib.apply_seccomp_filter.return_value = SECCOMP_SUCCESS
            mock_cdll.return_value = mock_lib

            injector = SeccompInjector(
                language="python", library_path="/mock/path.so"
            )

            # 测试快速连续操作
            iterations = 200
            operations = [
                lambda: injector.setup_no_new_privs(),
                lambda: injector.drop_privileges(1000, 1000),
                lambda: injector.apply_seccomp_filter(),
                lambda: injector.inject_seccomp_profile(1000, 1000),
            ]

            start_time = time.time()

            for i in range(iterations):
                operation = operations[i % len(operations)]
                operation()

            total_time = time.time() - start_time
            avg_time_per_operation = total_time / iterations

            # 平均每次操作应该很快
            assert avg_time_per_operation < 0.005  # 5ms内


class TestConcurrencyAndThreadSafety:
    """并发和线程安全测试"""

    def setup_method(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """测试后的清理"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_concurrent_injector_creation(self):
        """测试并发注入器创建"""
        manager = SecurityManager(library_dir=self.temp_dir)

        with mock.patch("src.security.SeccompInjector") as mock_injector_class:
            mock_injector_class.return_value = mock.MagicMock()

            def get_injector(language):
                return manager._get_injector_for_language(language)

            # 并发获取相同语言的注入器
            num_threads = 10
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=num_threads
            ) as executor:
                futures = [
                    executor.submit(get_injector, "python")
                    for _ in range(num_threads)
                ]
                results = [
                    future.result()
                    for future in concurrent.futures.as_completed(futures)
                ]

            # 所有结果应该是同一个实例（缓存效果）
            assert all(result is results[0] for result in results)

            # SeccompInjector构造函数应该只被调用一次
            assert mock_injector_class.call_count == 1

    def test_concurrent_different_languages(self):
        """测试并发不同语言处理"""
        manager = SecurityManager(library_dir=self.temp_dir)
        languages = ["python", "nodejs", "java", "cpp"] * 5  # 重复以增加并发

        with mock.patch("src.security.SeccompInjector") as mock_injector_class:
            mock_injector_class.return_value = mock.MagicMock()

            def get_injector(language):
                return manager._get_injector_for_language(language)

            # 并发获取不同语言的注入器
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=8
            ) as executor:
                futures = [
                    executor.submit(get_injector, lang) for lang in languages
                ]
                results = [
                    future.result()
                    for future in concurrent.futures.as_completed(futures)
                ]

            # 验证所有操作都成功完成
            assert len(results) == len(languages)

            # 每种唯一语言应该只创建一次注入器
            unique_languages = set(languages)
            assert mock_injector_class.call_count == len(unique_languages)

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_concurrent_security_operations(self):
        """测试并发安全操作"""
        manager = SecurityManager(library_dir=self.temp_dir)

        with mock.patch("src.security.SeccompInjector") as mock_injector_class:
            mock_injector = mock.MagicMock()
            mock_injector.setup_no_new_privs.return_value = None
            mock_injector.drop_privileges.return_value = None
            mock_injector.apply_seccomp_filter.return_value = None
            mock_injector_class.return_value = mock_injector

            def setup_security(uid_gid_pair):
                uid, gid = uid_gid_pair
                manager.setup_security_profile("python", uid, gid)
                return (uid, gid)

            # 并发设置安全配置
            uid_gid_pairs = [(1000 + i, 1000 + i) for i in range(20)]

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=5
            ) as executor:
                futures = [
                    executor.submit(setup_security, pair)
                    for pair in uid_gid_pairs
                ]
                results = [
                    future.result()
                    for future in concurrent.futures.as_completed(futures)
                ]

            # 验证所有操作都成功完成
            assert len(results) == len(uid_gid_pairs)
            assert set(results) == set(uid_gid_pairs)

            # 验证所有操作都被调用了
            assert mock_injector.setup_no_new_privs.call_count == len(
                uid_gid_pairs
            )
            assert mock_injector.drop_privileges.call_count == len(
                uid_gid_pairs
            )
            assert mock_injector.apply_seccomp_filter.call_count == len(
                uid_gid_pairs
            )

    def test_thread_safety_with_errors(self):
        """测试错误情况下的线程安全"""
        manager = SecurityManager(library_dir=self.temp_dir)

        with mock.patch("src.security.SeccompInjector") as mock_injector_class:
            # 模拟部分调用失败
            def side_effect(*args, **kwargs):
                if threading.current_thread().name.endswith("1"):
                    raise SeccompInjectionError(-1, "Simulated error")
                return mock.MagicMock()

            mock_injector_class.side_effect = side_effect

            def get_injector_safe(language):
                try:
                    return manager._get_injector_for_language(language)
                except Exception as e:
                    return e

            # 并发操作，部分会失败
            num_threads = 10
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=num_threads
            ) as executor:
                futures = [
                    executor.submit(get_injector_safe, "python")
                    for _ in range(num_threads)
                ]
                results = [
                    future.result()
                    for future in concurrent.futures.as_completed(futures)
                ]

            # 验证有成功和失败的结果
            successes = [r for r in results if not isinstance(r, Exception)]
            failures = [r for r in results if isinstance(r, Exception)]

            assert len(successes) > 0
            assert len(failures) > 0
            assert len(successes) + len(failures) == num_threads


class TestMemoryAndResourceUsage:
    """内存和资源使用测试"""

    def setup_method(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """测试后的清理"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_injector_cache_memory_usage(self):
        """测试注入器缓存内存使用"""
        manager = SecurityManager(library_dir=self.temp_dir)

        with mock.patch("src.security.SeccompInjector") as mock_injector_class:
            mock_injector_class.return_value = mock.MagicMock()

            # 创建大量不同语言的注入器
            languages = [f"lang_{i}" for i in range(100)]

            for lang in languages:
                try:
                    manager._get_injector_for_language(lang)
                except SecurityError:
                    # 预期的错误，因为这些语言不被支持
                    pass

            # 验证缓存大小合理
            # 只有支持的语言应该被缓存
            supported_languages = ["python", "nodejs", "java", "cpp"]

            # 缓存应该只包含实际支持的语言
            assert len(manager._injector_cache) <= len(supported_languages)

    def test_repeated_operations_memory_stability(self):
        """测试重复操作的内存稳定性"""
        manager = SecurityManager(library_dir=self.temp_dir)

        with mock.patch("src.security.SeccompInjector") as mock_injector_class:
            mock_injector = mock.MagicMock()
            mock_injector.setup_no_new_privs.return_value = None
            mock_injector.drop_privileges.return_value = None
            mock_injector.apply_seccomp_filter.return_value = None
            mock_injector_class.return_value = mock_injector

            # 重复大量操作
            iterations = 1000
            for i in range(iterations):
                try:
                    manager.setup_security_profile("python", 1000, 1000)
                    manager.setup_no_new_privs("python")
                    manager.drop_privileges("python", 1000, 1000)
                    manager.apply_seccomp_filter("python")
                except SecurityError:
                    pass  # 在非Linux系统上可能会失败

            # 验证缓存大小没有无限增长
            assert len(manager._injector_cache) <= 10  # 合理的上限

    @pytest.mark.skipif(
        not sys.platform.startswith("linux"), reason="Linux only"
    )
    def test_resource_cleanup_on_errors(self):
        """测试错误时的资源清理"""
        with mock.patch("ctypes.CDLL") as mock_cdll:
            # 模拟资源分配和清理
            mock_lib = mock.MagicMock()
            mock_cdll.return_value = mock_lib

            # 创建多个注入器，然后让它们失败
            injectors = []
            for i in range(10):
                try:
                    injector = SeccompInjector(
                        language="python", library_path=f"/mock/path_{i}.so"
                    )
                    injectors.append(injector)
                except Exception:
                    pass

            # 验证资源被正确分配
            assert len(injectors) > 0

            # 模拟垃圾回收
            injectors.clear()
            import gc

            gc.collect()

            # 在真实环境中，这里可以检查资源是否被正确释放
            # 由于使用mock，我们主要验证没有异常抛出


class TestStressAndEdgeCases:
    """压力测试和边界情况"""

    def setup_method(self):
        """测试前的设置"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """测试后的清理"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_extreme_uid_gid_values_performance(self):
        """测试极端UID/GID值的性能"""
        manager = SecurityManager(library_dir=self.temp_dir)

        with mock.patch("src.security.SeccompInjector") as mock_injector_class:
            mock_injector = mock.MagicMock()
            mock_injector.setup_no_new_privs.return_value = None
            mock_injector.drop_privileges.return_value = None
            mock_injector.apply_seccomp_filter.return_value = None
            mock_injector_class.return_value = mock_injector

            # 测试极端值
            extreme_values = [
                (0, 0),  # 最小值
                (65535, 65535),  # 16位最大值
                (4294967295, 4294967295),  # 32位最大值
            ]

            start_time = time.time()

            for uid, gid in extreme_values:
                try:
                    manager.setup_security_profile("python", uid, gid)
                except (SecurityError, OverflowError):
                    # 某些极端值可能不被支持
                    pass

            total_time = time.time() - start_time

            # 即使是极端值，处理时间也应该合理
            assert total_time < 1.0  # 1秒内完成

    def test_rapid_language_switching(self):
        """测试快速语言切换"""
        manager = SecurityManager(library_dir=self.temp_dir)
        languages = ["python", "nodejs", "java", "cpp"]

        with mock.patch("src.security.SeccompInjector") as mock_injector_class:
            mock_injector = mock.MagicMock()
            mock_injector.setup_no_new_privs.return_value = None
            mock_injector.drop_privileges.return_value = None
            mock_injector.apply_seccomp_filter.return_value = None
            mock_injector_class.return_value = mock_injector

            # 快速切换语言
            iterations = 200
            start_time = time.time()

            for i in range(iterations):
                lang = languages[i % len(languages)]
                try:
                    manager.setup_security_profile(lang, 1000, 1000)
                except SecurityError:
                    pass  # 在非Linux系统上可能会失败

            total_time = time.time() - start_time
            avg_time_per_switch = total_time / iterations

            # 平均每次切换应该很快
            assert avg_time_per_switch < 0.01  # 10ms内

    def test_error_recovery_performance(self):
        """测试错误恢复性能"""
        manager = SecurityManager(library_dir=self.temp_dir)

        with mock.patch("src.security.SeccompInjector") as mock_injector_class:
            # 模拟间歇性错误
            call_count = 0

            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count % 3 == 0:  # 每第3次调用失败
                    raise SeccompInjectionError(-1, "Intermittent error")
                return mock.MagicMock()

            mock_injector_class.side_effect = side_effect

            # 测试错误恢复
            iterations = 30
            success_count = 0
            error_count = 0

            start_time = time.time()

            for i in range(iterations):
                try:
                    manager._get_injector_for_language("python")
                    success_count += 1
                except Exception:
                    error_count += 1

            total_time = time.time() - start_time

            # 验证有成功和失败的情况
            assert success_count > 0
            assert error_count > 0
            assert success_count + error_count == iterations

            # 即使有错误，总时间也应该合理
            assert total_time < 2.0  # 2秒内完成


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
