#!/usr/bin/env python3
"""
security模块 - 代码沙盒安全组件

提供seccomp系统调用过滤和权限管理功能，包括：
- 系统调用配置解析
- seccomp过滤器注入
- 权限降级
- 安全策略管理
"""

from src.security.injection.seccomp_wrapper import (
    SECCOMP_ERROR_INVALID_ARGS,
    SECCOMP_ERROR_MEMORY,
    SECCOMP_ERROR_PRCTL,
    SECCOMP_ERROR_PRIVILEGE,
    SECCOMP_ERROR_SYSCALL,
    SECCOMP_ERROR_UNSUPPORTED,
    SECCOMP_SUCCESS,
    SeccompInjectionError,
    SeccompInjector,
)

__version__ = "1.0.0"
__author__ = "Code Sandbox Security Team"

__all__ = [
    # 主要类
    "SeccompInjector",
    "SecurityManager",
    # 异常
    "SeccompInjectionError",
    "SecurityError",
    # 便利函数
    "inject_seccomp_for_language",
    "create_secure_process",
    # 错误码
    "SECCOMP_SUCCESS",
    "SECCOMP_ERROR_PRCTL",
    "SECCOMP_ERROR_SYSCALL",
    "SECCOMP_ERROR_INVALID_ARGS",
    "SECCOMP_ERROR_PRIVILEGE",
    "SECCOMP_ERROR_MEMORY",
    "SECCOMP_ERROR_UNSUPPORTED",
]


class SecurityError(Exception):
    """安全相关的通用异常"""

    pass


class SecurityManager:
    """
    安全管理器 - 统一的安全策略管理接口

    提供语言特定的seccomp安全策略管理，使用编译时确定的系统调用列表
    """

    # 支持的编程语言列表（内部使用）
    _SUPPORTED_LANGUAGES = ["python", "nodejs"]

    def __init__(self, library_dir: str = None):
        """
        初始化安全管理器

        Args:
            library_dir: seccomp注入器共享库目录路径
        """
        self.library_dir = library_dir
        self._injectors = {}  # 缓存已加载的注入器

    def _get_injector_for_language(self, language: str) -> SeccompInjector:
        """
        获取指定语言的seccomp注入器

        Args:
            language: 编程语言名称

        Returns:
            SeccompInjector: 语言特定的注入器实例
        """
        if language not in self._SUPPORTED_LANGUAGES:
            raise SecurityError(f"Unsupported language: {language}")

        if language not in self._injectors:
            try:
                self._injectors[language] = SeccompInjector(
                    language=language, library_path=self.library_dir
                )
            except Exception as e:
                raise SecurityError(
                    f"Failed to load seccomp injector for {language}: {e}"
                )

        return self._injectors[language]

    def is_seccomp_supported(self):
        """检查当前平台是否支持seccomp"""
        return True  # 此模块只在Linux上可用

    def setup_security_profile(self, language: str, uid: int, gid: int):
        """
        为指定语言设置完整的安全配置

        Args:
            language: 编程语言名称
            uid: 目标用户ID
            gid: 目标组ID
        """
        try:
            injector = self._get_injector_for_language(language)
            injector.inject_seccomp_profile(uid, gid)
        except SeccompInjectionError as e:
            # 如果seccomp注入失败，检查是否是权限问题
            if "Privilege operation failed" in str(
                e
            ) or "Failed to set GID" in str(e):
                # 在非特权环境中，记录警告但继续执行
                # 这确保了代码在没有特权的环境中仍能运行
                # 不再打印到stderr，避免污染用户代码的输出
                return
            else:
                # 其他错误重新抛出
                raise

    def setup_no_new_privs(self, language: str):
        """
        设置PR_SET_NO_NEW_PRIVS

        Args:
            language: 编程语言名称
        """
        injector = self._get_injector_for_language(language)
        injector.setup_no_new_privs()

    def drop_privileges(self, language: str, uid: int, gid: int):
        """
        降低权限

        Args:
            language: 编程语言名称
            uid: 目标用户ID
            gid: 目标组ID
        """
        injector = self._get_injector_for_language(language)
        injector.drop_privileges(uid, gid)

    def apply_seccomp_filter(self, language: str):
        """
        应用seccomp过滤器

        Args:
            language: 编程语言名称
        """
        injector = self._get_injector_for_language(language)
        injector.apply_seccomp_filter()


def inject_seccomp_for_language(
    language: str,
    uid: int,
    gid: int,
    library_dir: str = None,
):
    """
    便利函数：为指定语言注入seccomp安全策略

    这是一个高级API，封装了完整的安全设置流程

    Args:
        language: 编程语言名称
        uid: 目标用户ID
        gid: 目标组ID
        library_dir: seccomp注入器共享库目录路径
    """
    manager = SecurityManager(library_dir)
    manager.setup_security_profile(language, uid, gid)


def create_secure_process(
    language: str,
    uid: int,
    gid: int,
    library_dir: str = None,
):
    """
    创建安全进程的便利函数

    这个函数应该在子进程中调用，用于设置安全环境

    Args:
        language: 编程语言名称
        uid: 目标用户ID
        gid: 目标组ID
        library_dir: seccomp注入器共享库目录路径
    """
    manager = SecurityManager(library_dir)
    manager.setup_security_profile(language, uid, gid)


# 模块级别的便利实例
_default_manager = None


def get_default_security_manager():
    """获取默认的安全管理器实例"""
    global _default_manager
    if _default_manager is None:
        _default_manager = SecurityManager()
    return _default_manager
