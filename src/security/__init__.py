#!/usr/bin/env python3
"""
security模块 - 代码沙盒安全组件

提供seccomp系统调用过滤和权限管理功能，包括：
- 系统调用配置解析
- seccomp过滤器注入
- 权限降级
- 安全策略管理
"""

from .syscalls.parser import SyscallConfigParser
from .injection.seccomp_wrapper import (
    SeccompInjector,
    SeccompInjectionError,
    inject_seccomp_for_language,
    SECCOMP_SUCCESS,
    SECCOMP_ERROR_PRCTL,
    SECCOMP_ERROR_SYSCALL,
    SECCOMP_ERROR_INVALID_ARGS,
    SECCOMP_ERROR_PRIVILEGE,
    SECCOMP_ERROR_MEMORY,
    SECCOMP_ERROR_UNSUPPORTED,
)

__version__ = "1.0.0"
__author__ = "Code Sandbox Security Team"

__all__ = [
    # 主要类
    "SyscallConfigParser",
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

    整合系统调用配置解析和seccomp注入功能，提供简化的API
    """

    def __init__(self, config_dir: str = None, library_path: str = None):
        """
        初始化安全管理器

        Args:
            config_dir: 系统调用配置文件目录
            library_path: seccomp注入器共享库路径
        """
        self.parser = SyscallConfigParser(config_dir)
        self.injector = None
        self.library_path = library_path

        # 延迟加载注入器（只在需要时加载）
        self._injector_loaded = False

    def _ensure_injector_loaded(self):
        """确保注入器已加载"""
        if not self._injector_loaded:
            try:
                self.injector = SeccompInjector(self.library_path)
                self._injector_loaded = True
            except Exception as e:
                raise SecurityError(f"Failed to load seccomp injector: {e}")

    def get_supported_languages(self):
        """获取支持的编程语言列表"""
        return self.parser.get_supported_languages()

    def get_syscalls_for_language(self, language: str):
        """获取指定语言的系统调用列表"""
        return self.parser.get_syscalls_for_language(language)

    def validate_syscalls(self, syscalls):
        """验证系统调用列表"""
        return self.parser.validate_syscalls(syscalls)

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
        # 获取系统调用列表
        syscalls = self.get_syscalls_for_language(language)
        if not syscalls:
            raise SecurityError(
                f"No syscall configuration found for language: {language}"
            )

        # 验证系统调用列表
        if not self.validate_syscalls(syscalls):
            raise SecurityError(
                f"Invalid syscall configuration for language: {language}"
            )

        # 加载并执行注入
        self._ensure_injector_loaded()
        self.injector.inject_seccomp_profile(syscalls, uid, gid)

    def setup_no_new_privs(self):
        """设置PR_SET_NO_NEW_PRIVS"""
        self._ensure_injector_loaded()
        self.injector.setup_no_new_privs()

    def drop_privileges(self, uid: int, gid: int):
        """降低权限"""
        self._ensure_injector_loaded()
        self.injector.drop_privileges(uid, gid)

    def apply_seccomp_filter(self, syscalls):
        """应用seccomp过滤器"""
        self._ensure_injector_loaded()
        self.injector.apply_seccomp_filter(syscalls)


def create_secure_process(
    language: str,
    uid: int,
    gid: int,
    config_dir: str = None,
    library_path: str = None,
):
    """
    创建安全进程的便利函数

    这个函数应该在子进程中调用，用于设置安全环境

    Args:
        language: 编程语言名称
        uid: 目标用户ID
        gid: 目标组ID
        config_dir: 系统调用配置文件目录
        library_path: seccomp注入器共享库路径
    """
    manager = SecurityManager(config_dir, library_path)
    manager.setup_security_profile(language, uid, gid)


# 模块级别的便利实例
_default_manager = None


def get_default_security_manager():
    """获取默认的安全管理器实例"""
    global _default_manager
    if _default_manager is None:
        _default_manager = SecurityManager()
    return _default_manager
