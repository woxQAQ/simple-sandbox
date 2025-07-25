"""
更新后的运行时seccomp注入器
使用BPF字节码和动态链接
"""

import ctypes
import json
import os
from pathlib import Path
from typing import Dict, List

# 加载libseccomp
try:
    libseccomp = ctypes.CDLL("libseccomp.so.2")
    SECCOMP_AVAILABLE = True
except OSError:
    libseccomp = None
    SECCOMP_AVAILABLE = False


class UpdatedSeccompInjector:
    """使用BPF字节码的seccomp注入器"""

    def __init__(self, bpf_dir: str = "build/seccomp"):
        self.bpf_dir = Path(bpf_dir)
        self.bpf_dir.mkdir(parents=True, exist_ok=True)

        # 加载BPF字节码
        self.bpf_programs: Dict[str, bytes] = {}
        self._load_bpf_programs()

        # 初始化libseccomp
        self._init_libseccomp()

    def _init_libseccomp(self):
        """初始化libseccomp"""
        if not SECCOMP_AVAILABLE:
            print("Warning: libseccomp not available, using fallback")
            return

        # 定义libseccomp函数原型
        self.libseccomp.seccomp_init.argtypes = [ctypes.c_uint32]
        self.libseccomp.seccomp_init.restype = ctypes.c_void_p

        self.libseccomp.seccomp_rule_add_exact.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_int,
            ctypes.c_uint,
        ]
        self.libseccomp.seccomp_rule_add_exact.restype = ctypes.c_int

        self.libseccomp.seccomp_load.argtypes = [ctypes.c_void_p]
        self.libseccomp.seccomp_load.restype = ctypes.c_int

        self.libseccomp.seccomp_release.argtypes = [ctypes.c_void_p]
        self.libseccomp.seccomp_release.restype = None

    def _load_bpf_programs(self):
        """加载预编译的BPF字节码"""
        from .bpf_compiler import BPFCompiler

        compiler = BPFCompiler()
        programs = compiler.compile_all()

        for name, program in programs.items():
            self.bpf_programs[name] = program

            # 保存到文件供调试
            bpf_path = self.bpf_dir / f"{name}.bpf"
            with open(bpf_path, "wb") as f:
                f.write(program)

    def apply_policy(self, language: str, pid: int = None) -> bool:
        """应用seccomp策略到进程"""
        if pid is None:
            pid = os.getpid()

        if language not in self.bpf_programs:
            print(f"No BPF program for {language}")
            return False

        bpf_bytes = self.bpf_programs[language]

        if SECCOMP_AVAILABLE:
            return self._apply_with_libseccomp(language)
        else:
            return self._apply_with_prctl(bpf_bytes)

    def _apply_with_libseccomp(self, language: str) -> bool:
        """使用libseccomp应用策略"""
        try:
            # 获取系统调用列表
            syscalls = self._get_syscalls_for_language(language)

            # 创建seccomp上下文
            ctx = self.libseccomp.seccomp_init(0)  # SCMP_ACT_KILL
            if not ctx:
                return False

            # 添加允许的syscall规则
            for syscall in syscalls:
                syscall_num = self._get_syscall_number(syscall)
                if syscall_num >= 0:
                    self.libseccomp.seccomp_rule_add_exact(
                        ctx,
                        0x7FFF0000,
                        syscall_num,
                        0,  # SCMP_ACT_ALLOW
                    )

            # 加载规则
            result = self.libseccomp.seccomp_load(ctx)
            self.libseccomp.seccomp_release(ctx)

            return result == 0

        except Exception as e:
            print(f"Failed to apply seccomp with libseccomp: {e}")
            return False

    def _apply_with_prctl(self, bpf_bytes: bytes) -> bool:
        """使用prctl系统调用应用BPF字节码"""
        try:
            import ctypes

            libc = ctypes.CDLL("libc.so.6")

            # 定义prctl常量
            PR_SET_SECCOMP = 22
            SECCOMP_MODE_FILTER = 2

            # 创建sock_fprog结构
            class sock_fprog(ctypes.Structure):
                _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.c_void_p)]

            # 创建BPF程序数组
            bpf_array = (ctypes.c_char * len(bpf_bytes)).from_buffer_copy(bpf_bytes)

            # 创建sock_fprog
            prog = sock_fprog()
            prog.len = len(bpf_bytes) // 8  # 每个指令8字节
            prog.filter = ctypes.cast(bpf_array, ctypes.c_void_p)

            # 应用seccomp
            result = libc.prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ctypes.byref(prog))

            return result == 0

        except Exception as e:
            print(f"Failed to apply seccomp with prctl: {e}")
            return False

    def _get_syscalls_for_language(self, language: str) -> List[str]:
        """获取特定语言的系统调用列表"""
        syscalls_file = Path(__file__).parent / "syscalls" / f"{language}_syscalls.json"
        if syscalls_file.exists():
            with open(syscalls_file) as f:
                return json.load(f)
        return []

    def _get_syscall_number(self, syscall_name: str) -> int:
        """获取系统调用号"""
        # 简化的系统调用号映射
        syscall_map = {
            "read": 0,
            "write": 1,
            "open": 2,
            "close": 3,
            "stat": 4,
            "fstat": 5,
            "lstat": 6,
            "poll": 7,
            "lseek": 8,
            "mmap": 9,
            "munmap": 11,
            "brk": 12,
            "rt_sigaction": 13,
            "rt_sigprocmask": 14,
            "ioctl": 16,
            "pread64": 17,
            "pwrite64": 18,
            "readv": 19,
            "writev": 20,
            "access": 21,
            "pipe": 22,
            "select": 23,
            "sched_yield": 24,
            "mremap": 25,
            "msync": 26,
            "mincore": 27,
            "madvise": 28,
            "shmget": 29,
            "shmat": 30,
            "shmctl": 31,
            "dup": 32,
            "dup2": 33,
            "pause": 34,
            "nanosleep": 35,
            "getitimer": 36,
            "alarm": 37,
            "setitimer": 38,
            "getpid": 39,
            "sendfile": 40,
            "socket": 41,
            "connect": 42,
            "accept": 43,
            "sendto": 44,
            "recvfrom": 45,
            "sendmsg": 46,
            "recvmsg": 47,
            "shutdown": 48,
            "bind": 49,
            "listen": 50,
            "getsockname": 51,
            "getpeername": 52,
            "socketpair": 53,
            "setsockopt": 54,
            "getsockopt": 55,
            "clone": 56,
            "fork": 57,
            "vfork": 58,
            "execve": 59,
            "exit": 60,
            "wait4": 61,
            "kill": 62,
            "uname": 63,
            "semget": 64,
            "semop": 65,
            "semctl": 66,
            "shmdt": 67,
            "msgget": 68,
            "msgsnd": 69,
            "msgrcv": 70,
            "msgctl": 71,
            "fcntl": 72,
            "flock": 73,
            "fsync": 74,
            "fdatasync": 75,
            "truncate": 76,
            "ftruncate": 77,
            "getdents": 78,
            "getcwd": 79,
            "chdir": 80,
            "fchdir": 81,
            "rename": 82,
            "mkdir": 83,
            "rmdir": 84,
            "creat": 85,
            "link": 86,
            "unlink": 87,
            "symlink": 88,
            "readlink": 89,
            "chmod": 90,
            "fchmod": 91,
            "chown": 92,
            "fchown": 93,
            "lchown": 94,
            "umask": 95,
            "gettimeofday": 96,
            "getrlimit": 97,
            "getrusage": 98,
            "sysinfo": 99,
            "times": 100,
            "ptrace": 101,
            "getuid": 102,
            "syslog": 103,
            "getgid": 104,
            "setuid": 105,
            "setgid": 106,
            "geteuid": 107,
            "getegid": 108,
            "setpgid": 109,
            "getppid": 110,
            "getpgrp": 111,
            "setsid": 112,
            "setreuid": 113,
            "setregid": 114,
            "getgroups": 115,
            "setgroups": 116,
            "setresuid": 117,
            "setresgid": 118,
            "getresuid": 119,
            "getresgid": 120,
            "getpgid": 121,
            "setfsuid": 122,
            "setfsgid": 123,
            "getsid": 124,
            "capget": 125,
            "capset": 126,
            "rt_sigpending": 127,
            "rt_sigtimedwait": 128,
            "rt_sigqueueinfo": 129,
            "rt_sigsuspend": 130,
            "sigaltstack": 131,
            "utime": 132,
            "mknod": 133,
            "uselib": 134,
            "personality": 135,
            "ustat": 136,
            "statfs": 137,
            "fstatfs": 138,
            "getpriority": 139,
            "setpriority": 140,
            "sched_setparam": 141,
            "sched_getparam": 142,
            "sched_setscheduler": 143,
            "sched_getscheduler": 144,
            "sched_get_priority_max": 145,
            "sched_get_priority_min": 146,
            "sched_rr_get_interval": 147,
            "mlock": 148,
            "munlock": 149,
            "mlockall": 150,
            "munlockall": 151,
            "vhangup": 152,
            "modify_ldt": 153,
            "pivot_root": 154,
            "_sysctl": 155,
            "prctl": 156,
            "arch_prctl": 158,
            "adjtimex": 159,
            "setrlimit": 160,
            "chroot": 161,
            "sync": 162,
            "acct": 163,
            "settimeofday": 164,
            "mount": 165,
            "umount2": 166,
            "swapon": 167,
            "swapoff": 168,
            "reboot": 169,
            "sethostname": 170,
            "setdomainname": 171,
            "iopl": 172,
            "ioperm": 173,
            "create_module": 174,
            "init_module": 175,
            "delete_module": 176,
            "get_kernel_syms": 177,
            "query_module": 178,
            "quotactl": 179,
            "nfsservctl": 180,
            "getpmsg": 181,
            "putpmsg": 182,
            "afs_syscall": 183,
            "tuxcall": 184,
            "security": 185,
            "gettid": 186,
            "readahead": 187,
            "setxattr": 188,
            "lsetxattr": 189,
            "fsetxattr": 190,
            "getxattr": 191,
            "lgetxattr": 192,
            "fgetxattr": 193,
            "listxattr": 194,
            "llistxattr": 195,
            "flistxattr": 196,
            "removexattr": 197,
            "lremovexattr": 198,
            "fremovexattr": 199,
            "tkill": 200,
            "time": 201,
            "futex": 202,
            "sched_setaffinity": 203,
            "sched_getaffinity": 204,
            "set_thread_area": 205,
            "io_setup": 206,
            "io_destroy": 207,
            "io_getevents": 208,
            "io_submit": 209,
            "io_cancel": 210,
            "get_thread_area": 211,
            "lookup_dcookie": 212,
            "epoll_create": 213,
            "remap_file_pages": 216,
            "getdents64": 217,
            "set_tid_address": 218,
            "restart_syscall": 219,
            "semtimedop": 220,
            "fadvise64": 221,
            "timer_create": 222,
            "timer_settime": 223,
            "timer_gettime": 224,
            "timer_getoverrun": 225,
            "timer_delete": 226,
            "clock_settime": 227,
            "clock_gettime": 228,
            "clock_getres": 229,
            "clock_nanosleep": 230,
            "exit_group": 231,
            "epoll_wait": 232,
            "epoll_ctl": 233,
            "tgkill": 234,
            "utimes": 235,
            "vserver": 236,
            "mbind": 237,
            "set_mempolicy": 238,
            "get_mempolicy": 239,
            "mq_open": 240,
            "mq_unlink": 241,
            "mq_timedsend": 242,
            "mq_timedreceive": 243,
            "mq_notify": 244,
            "mq_getsetattr": 245,
            "kexec_load": 246,
            "waitid": 247,
            "add_key": 248,
            "request_key": 249,
            "keyctl": 250,
            "ioprio_set": 251,
            "ioprio_get": 252,
            "inotify_init": 253,
            "inotify_add_watch": 254,
            "inotify_rm_watch": 255,
            "migrate_pages": 256,
            "openat": 257,
            "mkdirat": 258,
            "mknodat": 259,
            "fchownat": 260,
            "futimesat": 261,
            "newfstatat": 262,
            "unlinkat": 263,
            "renameat": 264,
            "linkat": 265,
            "symlinkat": 266,
            "readlinkat": 267,
            "fchmodat": 268,
            "faccessat": 269,
            "pselect6": 270,
            "ppoll": 271,
            "unshare": 272,
            "set_robust_list": 273,
            "get_robust_list": 274,
            "splice": 275,
            "tee": 276,
            "sync_file_range": 277,
            "vmsplice": 278,
            "move_pages": 279,
            "utimensat": 280,
            "epoll_pwait": 281,
            "signalfd": 282,
            "timerfd_create": 283,
            "eventfd": 284,
            "fallocate": 285,
            "timerfd_settime": 286,
            "timerfd_gettime": 287,
            "accept4": 288,
            "signalfd4": 289,
            "eventfd2": 290,
            "epoll_create1": 291,
            "dup3": 292,
            "pipe2": 293,
            "inotify_init1": 294,
            "preadv": 295,
            "pwritev": 296,
            "rt_tgsigqueueinfo": 297,
            "perf_event_open": 298,
            "recvmmsg": 299,
            "fanotify_init": 300,
            "fanotify_mark": 301,
            "prlimit64": 302,
            "name_to_handle_at": 303,
            "open_by_handle_at": 304,
            "clock_adjtime": 305,
            "syncfs": 306,
            "sendmmsg": 307,
            "setns": 308,
            "getcpu": 309,
            "process_vm_readv": 310,
            "process_vm_writev": 311,
            "kcmp": 312,
            "finit_module": 313,
            "sched_setattr": 314,
            "sched_getattr": 315,
            "renameat2": 316,
            "seccomp": 317,
            "getrandom": 318,
            "memfd_create": 319,
            "kexec_file_load": 320,
            "bpf": 321,
            "execveat": 322,
            "userfaultfd": 323,
            "membarrier": 324,
            "mlock2": 325,
            "copy_file_range": 326,
            "preadv2": 327,
            "pwritev2": 328,
            "pkey_mprotect": 329,
            "pkey_alloc": 330,
            "pkey_free": 331,
            "statx": 332,
            "io_pgetevents": 333,
            "rseq": 334,
        }

        return syscall_map.get(syscall_name, -1)


class UpdatedRuntimeSeccompManager:
    """更新后的运行时seccomp管理器"""

    def __init__(self):
        self.injector = UpdatedSeccompInjector()
        self.active_policies: Dict[int, str] = {}

    def setup_for_execution(self, language: str, pid: int = None) -> bool:
        """为代码执行设置seccomp"""
        if pid is None:
            pid = os.getpid()

        success = self.injector.apply_policy(language, pid)
        if success:
            self.active_policies[pid] = language
            print(f"✅ Applied {language} seccomp policy to process {pid}")
        else:
            print(f"❌ Failed to apply {language} seccomp policy")

        return success

    def cleanup_after_execution(self, pid: int = None) -> bool:
        """执行后清理seccomp策略"""
        if pid is None:
            pid = os.getpid()

        if pid in self.active_policies:
            del self.active_policies[pid]
            print(f"🧹 Cleaned up seccomp policy for process {pid}")
            return True

        return False

    def get_active_policies(self) -> Dict[int, str]:
        """获取活跃的策略"""
        return self.active_policies.copy()

    def is_policy_active(self, pid: int) -> bool:
        """检查进程是否有活跃策略"""
        return pid in self.active_policies


# 全局管理器
updated_seccomp_manager = UpdatedRuntimeSeccompManager()


if __name__ == "__main__":
    """测试新的seccomp系统"""
    from .bpf_compiler import BPFCompiler

    print("🧪 测试新的seccomp系统...")

    # 编译BPF程序
    compiler = BPFCompiler()
    programs = compiler.compile_all()

    for name, program in programs.items():
        print(f"✅ 编译 {name} BPF程序: {len(program)} 字节")

    # 测试应用策略
    manager = UpdatedRuntimeSeccompManager()

    print("\n🔒 测试策略应用...")
    success = manager.setup_for_execution("python")
    if success:
        print("✅ Python策略应用成功")
        manager.cleanup_after_execution()

    success = manager.setup_for_execution("nodejs")
    if success:
        print("✅ Node.js策略应用成功")
        manager.cleanup_after_execution()
