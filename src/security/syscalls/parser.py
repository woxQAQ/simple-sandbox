"""系统调用配置解析器"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class SyscallConfigParser:
    """解析和管理系统调用配置"""

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            # 默认使用build/seccomp目录
            self.config_dir = (
                Path(__file__).parent.parent.parent.parent / "build" / "seccomp"
            )
        else:
            self.config_dir = Path(config_dir)

        self._syscall_cache: Dict[str, Set[str]] = {}
        self._load_all_configs()

    def _load_all_configs(self):
        """加载所有语言的系统调用配置"""
        if not self.config_dir.exists():
            logger.warning(
                f"Syscall config directory not found: {self.config_dir}"
            )
            return

        for config_file in self.config_dir.glob("*.json"):
            if config_file.name.endswith("_bpf.c"):
                continue

            language = config_file.stem
            try:
                syscalls = self._parse_config_file(config_file)
                self._syscall_cache[language] = syscalls
                logger.info(f"Loaded {len(syscalls)} syscalls for {language}")
            except Exception as e:
                logger.error(f"Failed to load config for {language}: {e}")

    def _parse_config_file(self, config_file: Path) -> Set[str]:
        """解析单个配置文件"""
        with open(config_file, "r") as f:
            config = json.load(f)

        syscalls = set()

        # 解析seccomp格式的配置
        if "syscalls" in config:
            for syscall_group in config["syscalls"]:
                if (
                    "names" in syscall_group
                    and syscall_group.get("action") == "SCMP_ACT_ALLOW"
                ):
                    syscalls.update(syscall_group["names"])

        return syscalls

    def get_syscalls_for_language(self, language: str) -> List[str]:
        """获取指定语言的系统调用列表"""
        syscalls = self._syscall_cache.get(language, set())
        if not syscalls:
            logger.warning(f"No syscalls found for language: {language}")
            # 返回基础系统调用作为fallback
            return self._get_basic_syscalls()

        return sorted(list(syscalls))

    def _get_basic_syscalls(self) -> List[str]:
        """返回基础的系统调用列表"""
        return [
            "read",
            "write",
            "open",
            "openat",
            "close",
            "stat",
            "fstat",
            "lstat",
            "lseek",
            "mmap",
            "munmap",
            "mprotect",
            "brk",
            "rt_sigaction",
            "rt_sigprocmask",
            "getpid",
            "getuid",
            "getgid",
            "geteuid",
            "getegid",
            "exit",
            "exit_group",
        ]

    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return list(self._syscall_cache.keys())

    def validate_syscall_list(self, syscalls: List[str]) -> bool:
        """验证系统调用列表的有效性"""
        # 基本验证：检查是否包含必要的系统调用
        required_syscalls = {"exit", "exit_group", "read", "write"}
        syscall_set = set(syscalls)

        missing = required_syscalls - syscall_set
        if missing:
            logger.error(f"Missing required syscalls: {missing}")
            return False

        return True
