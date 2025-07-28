#!/usr/bin/env python3
"""
自动生成语言特定的系统调用定义
从JSON配置文件生成C代码中的syscall数组定义
"""

import json
import os
import sys
from typing import Dict, List

# 系统调用名称到编号的映射（x86_64）
SYSCALL_MAP = {
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
    "mprotect": 10,
    "munmap": 11,
    "brk": 12,
    "rt_sigaction": 13,
    "rt_sigprocmask": 14,
    "rt_sigreturn": 15,
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
    "getresuid": 118,
    "setresgid": 119,
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
    "sysfs": 139,
    "getpriority": 140,
    "setpriority": 141,
    "sched_setparam": 142,
    "sched_getparam": 143,
    "sched_setscheduler": 144,
    "sched_getscheduler": 145,
    "sched_get_priority_max": 146,
    "sched_get_priority_min": 147,
    "sched_rr_get_interval": 148,
    "mlock": 149,
    "munlock": 150,
    "mlockall": 151,
    "munlockall": 152,
    "vhangup": 153,
    "modify_ldt": 154,
    "pivot_root": 155,
    "_sysctl": 156,
    "prctl": 157,
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
    "epoll_ctl_old": 214,
    "epoll_wait_old": 215,
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
    "pidfd_send_signal": 424,
    "io_uring_setup": 425,
    "io_uring_enter": 426,
    "io_uring_register": 427,
    "open_tree": 428,
    "move_mount": 429,
    "fsopen": 430,
    "fsconfig": 431,
    "fsmount": 432,
    "fspick": 433,
    "pidfd_open": 434,
    "clone3": 435,
    "close_range": 436,
    "openat2": 437,
    "pidfd_getfd": 438,
    "faccessat2": 439,
    "process_madvise": 440,
    "epoll_pwait2": 441,
    "mount_setattr": 442,
    "quotactl_fd": 443,
    "landlock_create_ruleset": 444,
    "landlock_add_rule": 445,
    "landlock_restrict_self": 446,
    "memfd_secret": 447,
    "process_mrelease": 448,
    "futex_waitv": 449,
    "set_mempolicy_home_node": 450,
}


def load_syscall_config(config_path: str) -> Dict:
    """加载系统调用配置文件"""
    with open(config_path, "r") as f:
        return json.load(f)


def extract_syscall_names(config: Dict) -> List[str]:
    """从配置中提取系统调用名称"""
    syscall_names = []
    for syscall_group in config.get("syscalls", []):
        if syscall_group.get("action") == "SCMP_ACT_ALLOW":
            syscall_names.extend(syscall_group.get("names", []))
    return syscall_names


def generate_syscall_array(language: str, syscall_names: List[str]) -> str:
    """生成C代码中的系统调用数组定义"""
    syscall_numbers = []
    unknown_syscalls = []

    for name in syscall_names:
        if name in SYSCALL_MAP:
            syscall_numbers.append((SYSCALL_MAP[name], name))
        else:
            unknown_syscalls.append(name)

    if unknown_syscalls:
        print(
            f"Warning: Unknown syscalls for {language}: {unknown_syscalls}",
            file=sys.stderr,
        )

    # 按系统调用号排序
    syscall_numbers.sort()

    # 生成C代码
    lines = []
    lines.append(f"#elif defined(LANG_{language.upper()})")
    lines.append(f"/* {language.title()}语言的系统调用列表 */")
    lines.append("static const int ALLOWED_SYSCALLS[] = {")

    for num, name in syscall_numbers:
        lines.append(f"    {num:3d}, /* {name} */")

    lines.append("};")

    return "\n".join(lines)


def main():
    """主函数"""
    # 默认使用相对路径指向syscalls目录
    syscalls_dir = "../static"
    if len(sys.argv) > 1:
        syscalls_dir = sys.argv[1]

    # 查找所有语言配置文件
    config_files = []
    for filename in os.listdir(syscalls_dir):
        if filename.endswith(".json"):
            language = filename[:-5]  # 移除.json后缀
            config_files.append(
                (language, os.path.join(syscalls_dir, filename))
            )

    if not config_files:
        print(f"No JSON config files found in {syscalls_dir}", file=sys.stderr)
        sys.exit(1)

    # 生成所有语言的定义
    all_definitions = []

    for language, config_path in config_files:
        config = load_syscall_config(config_path)
        syscall_names = extract_syscall_names(config)
        definition = generate_syscall_array(language, syscall_names)
        all_definitions.append(definition)

    # 输出完整的条件编译块
    print("/* 语言特定的系统调用列表 - 编译时确定 */")

    # 按语言名称排序，确保一致的输出
    config_files.sort()

    for i, (language, config_path) in enumerate(config_files):
        config = load_syscall_config(config_path)
        syscall_names = extract_syscall_names(config)

        syscall_numbers = []
        unknown_syscalls = []

        for name in syscall_names:
            if name in SYSCALL_MAP:
                syscall_numbers.append((SYSCALL_MAP[name], name))
            else:
                unknown_syscalls.append(name)

        if unknown_syscalls:
            print(
                f"/* Warning: Unknown syscalls for {language}: {unknown_syscalls} */",
                file=sys.stderr,
            )

        # 按系统调用号排序
        syscall_numbers.sort()

        # 生成条件编译指令
        if i == 0:
            print(f"#ifdef LANG_{language.upper()}")
        else:
            print(f"#elif defined(LANG_{language.upper()})")

        print(f"/* {language.title()}语言的系统调用列表 */")
        print("static const int ALLOWED_SYSCALLS[] = {")

        for num, name in syscall_numbers:
            print(f"    {num:3d}, /* {name} */")

        print("};")

    print("#else")
    print('#error "Language not specified. Use -DLANG_PYTHON or -DLANG_NODEJS"')
    print("#endif")
    print()
    print(
        "#define SYSCALL_COUNT (sizeof(ALLOWED_SYSCALLS) / sizeof(ALLOWED_SYSCALLS[0]))"
    )


if __name__ == "__main__":
    main()
