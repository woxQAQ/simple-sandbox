"""
预编译BPF seccomp策略工厂
在构建时生成针对不同语言的seccomp策略
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class SeccompPolicy:
    """seccomp策略定义"""

    name: str
    syscalls: List[str]
    action: str = "SCMP_ACT_ALLOW"
    default_action: str = "SCMP_ACT_ERRNO"


class BPFGenerator:
    """BPF字节码生成器"""

    def __init__(self, output_dir: str = "build/seccomp"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_python_policy(self) -> Path:
        """生成Python专用seccomp策略"""
        python_syscalls = [
            # 基础系统调用
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
            # 内存管理
            "getpid",
            "getuid",
            "getgid",
            "geteuid",
            "getegid",
            "getppid",
            # 时间管理
            "gettimeofday",
            "clock_gettime",
            "nanosleep",
            "time",
            # 进程控制
            "exit",
            "exit_group",
            "wait4",
            "clone",
            "fork",
            "vfork",
            # 文件操作
            "readlink",
            "readlinkat",
            "access",
            "faccessat",
            "fcntl",
            "ioctl",
            # 网络（限制访问）
            "socket",
            "connect",
            "bind",
            "listen",
            "accept",
            "accept4",
            # Python特定
            "getcwd",
            "chdir",
            "fchdir",
            "umask",
            "dup",
            "dup2",
            "dup3",
            # 信号
            "kill",
            "tkill",
            "tgkill",
            "signalfd",
            "signalfd4",
            # 其他必需
            "pipe",
            "pipe2",
            "poll",
            "select",
            "epoll_create",
            "epoll_ctl",
            "epoll_wait",
        ]

        policy = SeccompPolicy("python", python_syscalls)
        return self._generate_bpf(policy)

    def generate_nodejs_policy(self) -> Path:
        """生成Node.js专用seccomp策略"""
        nodejs_syscalls = [
            # 基础系统调用
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
            # Node.js特定
            "epoll_create",
            "epoll_ctl",
            "epoll_wait",
            "eventfd",
            "eventfd2",
            "timerfd_create",
            "timerfd_settime",
            "timerfd_gettime",
            # 文件系统
            "readlink",
            "readlinkat",
            "access",
            "faccessat",
            "fcntl",
            "ioctl",
            # 网络
            "socket",
            "connect",
            "bind",
            "listen",
            "accept",
            "accept4",
            "sendto",
            "recvfrom",
            "sendmsg",
            "recvmsg",
            "shutdown",
            # 进程
            "execve",
            "execveat",
            "wait4",
            "exit",
            "exit_group",
        ]

        policy = SeccompPolicy("nodejs", nodejs_syscalls)
        return self._generate_bpf(policy)

    def _generate_bpf(self, policy: SeccompPolicy) -> Path:
        """生成seccomp策略文件"""
        config = {
            "defaultAction": policy.default_action,
            "architectures": ["SCMP_ARCH_X86_64"],
            "syscalls": [{"names": policy.syscalls, "action": policy.action}],
        }

        config_path = self.output_dir / f"{policy.name}.json"

        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        return config_path

    def _generate_simple_bpf(self, policy: SeccompPolicy, output_path: Path):
        """简化BPF生成（备用方案）"""
        # 创建简化的BPF程序定义
        bpf_def = {
            "policy": policy.name,
            "syscalls": policy.syscalls,
            "default_action": policy.default_action,
            "action": policy.action,
        }

        with open(output_path, "w") as f:
            json.dump(bpf_def, f)

        return output_path

    def build_all(self) -> Dict[str, Path]:
        """构建所有策略"""
        policies = {}

        policies["python"] = self.generate_python_policy()
        policies["nodejs"] = self.generate_nodejs_policy()

        return policies


if __name__ == "__main__":
    generator = BPFGenerator()
    policies = generator.build_all()

    for name, path in policies.items():
        print(f"Generated {name} policy: {path}")
