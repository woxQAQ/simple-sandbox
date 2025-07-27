#!/usr/bin/env python3
"""
seccomp注入器的Python包装器
提供Python接口来调用C实现的seccomp注入功能
"""

import ctypes
import sys
from typing import List, Optional
from pathlib import Path

# 错误码常量
SECCOMP_SUCCESS = 0
SECCOMP_ERROR_PRCTL = -1
SECCOMP_ERROR_SYSCALL = -2
SECCOMP_ERROR_INVALID_ARGS = -3
SECCOMP_ERROR_PRIVILEGE = -4
SECCOMP_ERROR_MEMORY = -5
SECCOMP_ERROR_UNSUPPORTED = -6

ERROR_MESSAGES = {
    SECCOMP_SUCCESS: "Success",
    SECCOMP_ERROR_PRCTL: "prctl() system call failed",
    SECCOMP_ERROR_SYSCALL: "seccomp system call failed",
    SECCOMP_ERROR_INVALID_ARGS: "Invalid arguments",
    SECCOMP_ERROR_PRIVILEGE: "Privilege operation failed",
    SECCOMP_ERROR_MEMORY: "Memory allocation failed",
    SECCOMP_ERROR_UNSUPPORTED: "Unsupported platform",
}


class SeccompInjectionError(Exception):
    """seccomp注入相关的异常"""

    def __init__(self, error_code: int, message: str = None):
        self.error_code = error_code
        self.message = message or ERROR_MESSAGES.get(
            error_code, "Unknown error"
        )
        super().__init__(
            f"Seccomp injection failed: {self.message} (code: {error_code})"
        )


class SeccompInjector:
    """seccomp注入器类"""

    def __init__(self, library_path: Optional[str] = None):
        """
        初始化seccomp注入器

        Args:
            library_path: 共享库路径，如果为None则自动查找
        """
        self._lib = None
        self._load_library(library_path)
        self._setup_function_signatures()

    def _find_library_path(self) -> str:
        """查找seccomp注入器共享库"""
        # 可能的库文件名
        lib_names = [
            "libseccomp_injector.so",
            "libseccomp_injector.dylib",  # macOS (虽然不支持seccomp)
            "seccomp_injector.dll",  # Windows (虽然不支持seccomp)
        ]

        # 搜索路径
        search_paths = [
            # 相对于当前文件的路径
            Path(__file__).parent.parent / "bpf",
            # 构建目录
            Path(__file__).parent.parent.parent.parent / "build" / "lib",
            # 系统库路径
            Path("/usr/local/lib"),
            Path("/usr/lib"),
        ]

        for search_path in search_paths:
            for lib_name in lib_names:
                lib_path = search_path / lib_name
                if lib_path.exists():
                    return str(lib_path)

        raise FileNotFoundError(
            f"Could not find seccomp injector library. Searched in: {search_paths}"
        )

    def _load_library(self, library_path: Optional[str]):
        """加载共享库"""
        if library_path is None:
            library_path = self._find_library_path()

        try:
            self._lib = ctypes.CDLL(library_path)
        except OSError as e:
            raise SeccompInjectionError(
                SECCOMP_ERROR_UNSUPPORTED,
                f"Failed to load library {library_path}: {e}",
            )

    def _setup_function_signatures(self):
        """设置C函数的签名"""
        if not self._lib:
            return

        # setup_no_new_privs() -> int
        self._lib.setup_no_new_privs.argtypes = []
        self._lib.setup_no_new_privs.restype = ctypes.c_int

        # drop_privileges(uid_t uid, gid_t gid) -> int
        self._lib.drop_privileges.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
        self._lib.drop_privileges.restype = ctypes.c_int

        # apply_seccomp_filter(const int* syscalls, size_t syscall_count) -> int
        self._lib.apply_seccomp_filter.argtypes = [
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_size_t,
        ]
        self._lib.apply_seccomp_filter.restype = ctypes.c_int

        # inject_seccomp_profile(const int* syscalls, size_t syscall_count, uid_t uid, gid_t gid) -> int
        self._lib.inject_seccomp_profile.argtypes = [
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_size_t,
            ctypes.c_uint32,
            ctypes.c_uint32,
        ]
        self._lib.inject_seccomp_profile.restype = ctypes.c_int

        # get_error_description(int error_code) -> const char*
        self._lib.get_error_description.argtypes = [ctypes.c_int]
        self._lib.get_error_description.restype = ctypes.c_char_p

    def setup_no_new_privs(self) -> None:
        """设置PR_SET_NO_NEW_PRIVS"""
        if not self._lib:
            raise SeccompInjectionError(SECCOMP_ERROR_UNSUPPORTED)

        result = self._lib.setup_no_new_privs()
        if result != SECCOMP_SUCCESS:
            raise SeccompInjectionError(result)

    def drop_privileges(self, uid: int, gid: int) -> None:
        """降低权限到指定的UID和GID"""
        if not self._lib:
            raise SeccompInjectionError(SECCOMP_ERROR_UNSUPPORTED)

        result = self._lib.drop_privileges(
            ctypes.c_uint32(uid), ctypes.c_uint32(gid)
        )
        if result != SECCOMP_SUCCESS:
            raise SeccompInjectionError(result)

    def apply_seccomp_filter(self, syscalls: List[int]) -> None:
        """应用seccomp过滤器"""
        if not self._lib:
            raise SeccompInjectionError(SECCOMP_ERROR_UNSUPPORTED)

        if not syscalls:
            raise SeccompInjectionError(
                SECCOMP_ERROR_INVALID_ARGS, "Syscall list cannot be empty"
            )

        # 转换为C数组
        syscall_array = (ctypes.c_int * len(syscalls))(*syscalls)

        result = self._lib.apply_seccomp_filter(syscall_array, len(syscalls))
        if result != SECCOMP_SUCCESS:
            raise SeccompInjectionError(result)

    def inject_seccomp_profile(
        self, syscalls: List[int], uid: int, gid: int
    ) -> None:
        """完整的seccomp注入流程"""
        if not self._lib:
            raise SeccompInjectionError(SECCOMP_ERROR_UNSUPPORTED)

        if not syscalls:
            raise SeccompInjectionError(
                SECCOMP_ERROR_INVALID_ARGS, "Syscall list cannot be empty"
            )

        # 转换为C数组
        syscall_array = (ctypes.c_int * len(syscalls))(*syscalls)

        result = self._lib.inject_seccomp_profile(
            syscall_array,
            len(syscalls),
            ctypes.c_uint32(uid),
            ctypes.c_uint32(gid),
        )
        if result != SECCOMP_SUCCESS:
            raise SeccompInjectionError(result)

    def get_error_description(self, error_code: int) -> str:
        """获取错误描述"""
        if not self._lib:
            return ERROR_MESSAGES.get(error_code, "Unknown error")

        desc = self._lib.get_error_description(ctypes.c_int(error_code))
        if desc:
            return desc.decode("utf-8")
        return "Unknown error"

    @staticmethod
    def is_supported() -> bool:
        """检查当前平台是否支持seccomp"""
        return sys.platform.startswith("linux")


# 便利函数
def inject_seccomp_for_language(
    language: str, uid: int, gid: int, library_path: Optional[str] = None
) -> None:
    """
    为指定语言注入seccomp配置

    Args:
        language: 编程语言名称 (如 'python', 'nodejs')
        uid: 目标用户ID
        gid: 目标组ID
        library_path: 共享库路径
    """
    from ..syscalls.parser import SyscallConfigParser

    # 加载系统调用配置
    parser = SyscallConfigParser()
    syscalls = parser.get_syscalls_for_language(language)

    if not syscalls:
        raise SeccompInjectionError(
            SECCOMP_ERROR_INVALID_ARGS,
            f"No syscall configuration found for language: {language}",
        )

    # 执行注入
    injector = SeccompInjector(library_path)
    injector.inject_seccomp_profile(syscalls, uid, gid)


if __name__ == "__main__":
    # 简单的测试
    if SeccompInjector.is_supported():
        print("Seccomp is supported on this platform")
        try:
            injector = SeccompInjector()
            print("Seccomp injector loaded successfully")
        except Exception as e:
            print(f"Failed to load seccomp injector: {e}")
    else:
        print("Seccomp is not supported on this platform")
