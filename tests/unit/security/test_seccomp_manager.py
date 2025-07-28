#!/usr/bin/env python3
"""
Seccomp管理器单元测试
测试seccomp安全模块功能
"""

import pytest
import json
from unittest.mock import patch, mock_open

from src.security.seccomp_manager import SeccompManager
from src.runtime.models import Language


class TestSeccompManager:
    """Seccomp管理器测试"""
    
    @pytest.fixture
    def manager(self):
        """创建Seccomp管理器实例"""
        return SeccompManager()
    
    @pytest.fixture
    def sample_python_config(self):
        """Python配置样例"""
        return {
            "defaultAction": "SCMP_ACT_ERRNO",
            "allowedSyscalls": [
                "read", "write", "open", "close", "stat", "fstat", "lstat",
                "poll", "lseek", "mmap", "mprotect", "munmap", "brk",
                "rt_sigaction", "rt_sigprocmask", "rt_sigreturn", "ioctl",
                "pread64", "pwrite64", "readv", "writev", "access", "pipe",
                "select", "sched_yield", "mremap", "msync", "mincore",
                "madvise", "shmget", "shmat", "shmctl", "dup", "dup2",
                "pause", "nanosleep", "getitimer", "alarm", "setitimer",
                "getpid", "sendfile", "socket", "connect", "accept",
                "sendto", "recvfrom", "sendmsg", "recvmsg", "shutdown",
                "bind", "listen", "getsockname", "getpeername", "socketpair",
                "setsockopt", "getsockopt", "clone", "fork", "vfork",
                "execve", "exit", "wait4", "kill", "uname", "semget",
                "semop", "semctl", "shmdt", "msgget", "msgsnd", "msgrcv",
                "msgctl", "fcntl", "flock", "fsync", "fdatasync",
                "truncate", "ftruncate", "getdents", "getcwd", "chdir",
                "fchdir", "rename", "mkdir", "rmdir", "creat", "link",
                "unlink", "symlink", "readlink", "chmod", "fchmod",
                "chown", "fchown", "lchown", "umask", "gettimeofday",
                "getrlimit", "getrusage", "sysinfo", "times", "ptrace",
                "getuid", "syslog", "getgid", "setuid", "setgid",
                "geteuid", "getegid", "setpgid", "getppid", "getpgrp",
                "setsid", "setreuid", "setregid", "getgroups", "setgroups",
                "setresuid", "getresuid", "setresgid", "getresgid",
                "getpgid", "setfsuid", "setfsgid", "getsid", "capget",
                "capset", "rt_sigpending", "rt_sigtimedwait", "rt_sigqueueinfo",
                "rt_sigsuspend", "sigaltstack", "utime", "mknod",
                "uselib", "personality", "ustat", "statfs", "fstatfs",
                "sysfs", "getpriority", "setpriority", "sched_setparam",
                "sched_getparam", "sched_setscheduler", "sched_getscheduler",
                "sched_get_priority_max", "sched_get_priority_min",
                "sched_rr_get_interval", "mlock", "munlock", "mlockall",
                "munlockall", "vhangup", "modify_ldt", "pivot_root",
                "_sysctl", "prctl", "arch_prctl", "adjtimex", "setrlimit",
                "chroot", "sync", "acct", "settimeofday", "mount",
                "umount2", "swapon", "swapoff", "reboot", "sethostname",
                "setdomainname", "iopl", "ioperm", "create_module",
                "init_module", "delete_module", "get_kernel_syms",
                "query_module", "quotactl", "nfsservctl", "getpmsg",
                "putpmsg", "afs_syscall", "tuxcall", "security",
                "gettid", "readahead", "setxattr", "lsetxattr", "fsetxattr",
                "getxattr", "lgetxattr", "fgetxattr", "listxattr",
                "llistxattr", "flistxattr", "removexattr", "lremovexattr",
                "fremovexattr", "tkill", "time", "futex", "sched_setaffinity",
                "sched_getaffinity", "set_thread_area", "io_setup",
                "io_destroy", "io_getevents", "io_submit", "io_cancel",
                "get_thread_area", "lookup_dcookie", "epoll_create",
                "epoll_ctl_old", "epoll_wait_old", "remap_file_pages",
                "getdents64", "set_tid_address", "restart_syscall",
                "semtimedop", "fadvise64", "timer_create", "timer_settime",
                "timer_gettime", "timer_getoverrun", "timer_delete",
                "clock_settime", "clock_gettime", "clock_getres",
                "clock_nanosleep", "exit_group", "epoll_wait", "epoll_ctl",
                "tgkill", "utimes", "vserver", "mbind", "set_mempolicy",
                "get_mempolicy", "mq_open", "mq_unlink", "mq_timedsend",
                "mq_timedreceive", "mq_notify", "mq_getsetattr", "kexec_load",
                "waitid", "add_key", "request_key", "keyctl", "ioprio_set",
                "ioprio_get", "inotify_init", "inotify_add_watch",
                "inotify_rm_watch", "migrate_pages", "openat", "mkdirat",
                "mknodat", "fchownat", "futimesat", "newfstatat", "unlinkat",
                "renameat", "linkat", "symlinkat", "readlinkat", "fchmodat",
                "faccessat", "pselect6", "ppoll", "unshare", "set_robust_list",
                "get_robust_list", "splice", "tee", "sync_file_range",
                "vmsplice", "move_pages", "utimensat", "epoll_pwait",
                "signalfd", "timerfd_create", "eventfd", "fallocate",
                "timerfd_settime", "timerfd_gettime", "accept4", "signalfd4",
                "eventfd2", "epoll_create1", "dup3", "pipe2", "inotify_init1",
                "preadv", "pwritev", "rt_tgsigqueueinfo", "perf_event_open",
                "recvmmsg", "fanotify_init", "fanotify_mark", "prlimit64",
                "name_to_handle_at", "open_by_handle_at", "clock_adjtime",
                "syncfs", "sendmmsg", "setns", "getcpu", "process_vm_readv",
                "process_vm_writev", "kcmp", "finit_module"
            ]
        }
    
    @pytest.fixture
    def sample_nodejs_config(self):
        """Node.js配置样例"""
        return {
            "defaultAction": "SCMP_ACT_ERRNO",
            "allowedSyscalls": [
                "read", "write", "open", "close", "stat", "fstat", "lstat",
                "poll", "lseek", "mmap", "mprotect", "munmap", "brk",
                "rt_sigaction", "rt_sigprocmask", "rt_sigreturn", "ioctl",
                "pread64", "pwrite64", "readv", "writev", "access", "pipe",
                "select", "sched_yield", "mremap", "msync", "mincore",
                "madvise", "dup", "dup2", "pause", "nanosleep", "getitimer",
                "alarm", "setitimer", "getpid", "sendfile", "socket",
                "connect", "accept", "sendto", "recvfrom", "sendmsg",
                "recvmsg", "shutdown", "bind", "listen", "getsockname",
                "getpeername", "socketpair", "setsockopt", "getsockopt",
                "clone", "fork", "vfork", "execve", "exit", "wait4", "kill",
                "uname", "fcntl", "flock", "fsync", "fdatasync", "truncate",
                "ftruncate", "getdents", "getcwd", "chdir", "fchdir",
                "rename", "mkdir", "rmdir", "creat", "link", "unlink",
                "symlink", "readlink", "chmod", "fchmod", "chown", "fchown",
                "lchown", "umask", "gettimeofday", "getrlimit", "getrusage",
                "sysinfo", "times", "ptrace", "getuid", "syslog", "getgid",
                "setuid", "setgid", "geteuid", "getegid", "setpgid",
                "getppid", "getpgrp", "setsid", "setreuid", "setregid",
                "getgroups", "setgroups", "setresuid", "getresuid",
                "setresgid", "getresgid", "getpgid", "setfsuid", "setfsgid",
                "getsid", "capget", "capset", "rt_sigpending",
                "rt_sigtimedwait", "rt_sigqueueinfo", "rt_sigsuspend",
                "sigaltstack", "utime", "mknod", "personality", "ustat",
                "statfs", "fstatfs", "sysfs", "getpriority", "setpriority",
                "sched_setparam", "sched_getparam", "sched_setscheduler",
                "sched_getscheduler", "sched_get_priority_max",
                "sched_get_priority_min", "sched_rr_get_interval", "mlock",
                "munlock", "mlockall", "munlockall", "vhangup", "modify_ldt",
                "pivot_root", "_sysctl", "prctl", "arch_prctl", "adjtimex",
                "setrlimit", "chroot", "sync", "acct", "settimeofday",
                "gettid", "readahead", "setxattr", "lsetxattr", "fsetxattr",
                "getxattr", "lgetxattr", "fgetxattr", "listxattr",
                "llistxattr", "flistxattr", "removexattr", "lremovexattr",
                "fremovexattr", "tkill", "time", "futex", "sched_setaffinity",
                "sched_getaffinity", "set_thread_area", "io_setup",
                "io_destroy", "io_getevents", "io_submit", "io_cancel",
                "get_thread_area", "lookup_dcookie", "epoll_create",
                "remap_file_pages", "getdents64", "set_tid_address",
                "restart_syscall", "semtimedop", "fadvise64", "timer_create",
                "timer_settime", "timer_gettime", "timer_getoverrun",
                "timer_delete", "clock_settime", "clock_gettime",
                "clock_getres", "clock_nanosleep", "exit_group", "epoll_wait",
                "epoll_ctl", "tgkill", "utimes", "mbind", "set_mempolicy",
                "get_mempolicy", "mq_open", "mq_unlink", "mq_timedsend",
                "mq_timedreceive", "mq_notify", "mq_getsetattr", "waitid",
                "add_key", "request_key", "keyctl", "ioprio_set", "ioprio_get",
                "inotify_init", "inotify_add_watch", "inotify_rm_watch",
                "migrate_pages", "openat", "mkdirat", "mknodat", "fchownat",
                "futimesat", "newfstatat", "unlinkat", "renameat", "linkat",
                "symlinkat", "readlinkat", "fchmodat", "faccessat", "pselect6",
                "ppoll", "unshare", "set_robust_list", "get_robust_list",
                "splice", "tee", "sync_file_range", "vmsplice", "move_pages",
                "utimensat", "epoll_pwait", "signalfd", "timerfd_create",
                "eventfd", "fallocate", "timerfd_settime", "timerfd_gettime",
                "accept4", "signalfd4", "eventfd2", "epoll_create1", "dup3",
                "pipe2", "inotify_init1", "preadv", "pwritev",
                "rt_tgsigqueueinfo", "perf_event_open", "recvmmsg",
                "fanotify_init", "fanotify_mark", "prlimit64",
                "name_to_handle_at", "open_by_handle_at", "clock_adjtime",
                "syncfs", "sendmmsg", "setns", "getcpu", "process_vm_readv",
                "process_vm_writev", "kcmp", "finit_module"
            ]
        }
    
    @pytest.mark.unit
    def test_manager_initialization(self, manager):
        """测试管理器初始化"""
        assert isinstance(manager, SeccompManager)
        assert hasattr(manager, '_config_cache')
        assert hasattr(manager, '_static_dir')
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_python(self, mock_file, mock_exists, manager, sample_python_config):
        """测试加载Python配置"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(sample_python_config)
        
        config = manager.load_config(Language.PYTHON)
        
        assert config["defaultAction"] == "SCMP_ACT_ERRNO"
        assert "read" in config["allowedSyscalls"]
        assert "write" in config["allowedSyscalls"]
        assert "execve" in config["allowedSyscalls"]
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_nodejs(self, mock_file, mock_exists, manager, sample_nodejs_config):
        """测试加载Node.js配置"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(sample_nodejs_config)
        
        config = manager.load_config(Language.NODEJS)
        
        assert config["defaultAction"] == "SCMP_ACT_ERRNO"
        assert "read" in config["allowedSyscalls"]
        assert "write" in config["allowedSyscalls"]
        assert "execve" in config["allowedSyscalls"]
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    def test_load_config_file_not_found(self, mock_exists, manager):
        """测试配置文件不存在"""
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError, match="配置文件不存在|Config file not found"):
            manager.load_config(Language.PYTHON)
    
    @pytest.mark.unit
    def test_load_config_unsupported_language(self, manager):
        """测试不支持的语言"""
        with pytest.raises(ValueError, match="不支持的语言|Unsupported language"):
            manager.load_config("unsupported_language")
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_invalid_json(self, mock_file, mock_exists, manager):
        """测试无效的JSON配置"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "invalid json content"
        
        with pytest.raises(json.JSONDecodeError):
            manager.load_config(Language.PYTHON)
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_config_caching(self, mock_file, mock_exists, manager, sample_python_config):
        """测试配置缓存"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(sample_python_config)
        
        # 第一次加载
        config1 = manager.load_config(Language.PYTHON)
        
        # 第二次加载应该使用缓存
        config2 = manager.load_config(Language.PYTHON)
        
        assert config1 is config2
        # 文件应该只被读取一次
        assert mock_file.call_count == 1
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_allowed_syscalls_python(self, mock_file, mock_exists, manager, sample_python_config):
        """测试获取Python允许的系统调用"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(sample_python_config)
        
        syscalls = manager.get_allowed_syscalls(Language.PYTHON)
        
        assert isinstance(syscalls, list)
        assert "read" in syscalls
        assert "write" in syscalls
        assert "execve" in syscalls
        assert len(syscalls) > 100  # Python需要很多系统调用
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_allowed_syscalls_nodejs(self, mock_file, mock_exists, manager, sample_nodejs_config):
        """测试获取Node.js允许的系统调用"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(sample_nodejs_config)
        
        syscalls = manager.get_allowed_syscalls(Language.NODEJS)
        
        assert isinstance(syscalls, list)
        assert "read" in syscalls
        assert "write" in syscalls
        assert "execve" in syscalls
        assert len(syscalls) > 100  # Node.js也需要很多系统调用
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_default_action(self, mock_file, mock_exists, manager, sample_python_config):
        """测试获取默认动作"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(sample_python_config)
        
        action = manager.get_default_action(Language.PYTHON)
        
        assert action == "SCMP_ACT_ERRNO"
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_is_syscall_allowed_true(self, mock_file, mock_exists, manager, sample_python_config):
        """测试系统调用是否被允许（允许的情况）"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(sample_python_config)
        
        assert manager.is_syscall_allowed(Language.PYTHON, "read") is True
        assert manager.is_syscall_allowed(Language.PYTHON, "write") is True
        assert manager.is_syscall_allowed(Language.PYTHON, "execve") is True
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_is_syscall_allowed_false(self, mock_file, mock_exists, manager, sample_python_config):
        """测试系统调用是否被允许（不允许的情况）"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(sample_python_config)
        
        # 假设这些系统调用不在允许列表中
        assert manager.is_syscall_allowed(Language.PYTHON, "dangerous_syscall") is False
        assert manager.is_syscall_allowed(Language.PYTHON, "nonexistent_syscall") is False
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_validate_config_valid(self, mock_file, mock_exists, manager, sample_python_config):
        """测试有效配置验证"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(sample_python_config)
        
        # 有效配置不应该抛出异常
        manager._validate_config(sample_python_config)
    
    @pytest.mark.unit
    def test_validate_config_missing_default_action(self, manager):
        """测试缺少默认动作的配置验证"""
        invalid_config = {
            "allowedSyscalls": ["read", "write"]
        }
        
        with pytest.raises(ValueError, match="配置缺少必需字段|Missing required field"):
            manager._validate_config(invalid_config)
    
    @pytest.mark.unit
    def test_validate_config_missing_allowed_syscalls(self, manager):
        """测试缺少允许系统调用的配置验证"""
        invalid_config = {
            "defaultAction": "SCMP_ACT_ERRNO"
        }
        
        with pytest.raises(ValueError, match="配置缺少必需字段|Missing required field"):
            manager._validate_config(invalid_config)
    
    @pytest.mark.unit
    def test_validate_config_invalid_default_action(self, manager):
        """测试无效默认动作的配置验证"""
        invalid_config = {
            "defaultAction": "INVALID_ACTION",
            "allowedSyscalls": ["read", "write"]
        }
        
        with pytest.raises(ValueError, match="无效的默认动作|Invalid default action"):
            manager._validate_config(invalid_config)
    
    @pytest.mark.unit
    def test_validate_config_empty_syscalls(self, manager):
        """测试空系统调用列表的配置验证"""
        invalid_config = {
            "defaultAction": "SCMP_ACT_ERRNO",
            "allowedSyscalls": []
        }
        
        with pytest.raises(ValueError, match="允许的系统调用列表不能为空|Allowed syscalls list cannot be empty"):
            manager._validate_config(invalid_config)
    
    @pytest.mark.unit
    def test_validate_config_non_list_syscalls(self, manager):
        """测试非列表类型的系统调用配置验证"""
        invalid_config = {
            "defaultAction": "SCMP_ACT_ERRNO",
            "allowedSyscalls": "not_a_list"
        }
        
        with pytest.raises(ValueError, match="允许的系统调用必须是列表|Allowed syscalls must be a list"):
            manager._validate_config(invalid_config)
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_config_path(self, mock_file, mock_exists, manager):
        """测试获取配置文件路径"""
        python_path = manager._get_config_path(Language.PYTHON)
        nodejs_path = manager._get_config_path(Language.NODEJS)
        
        assert python_path.name == "python.json"
        assert nodejs_path.name == "nodejs.json"
        assert "static" in str(python_path)
        assert "static" in str(nodejs_path)
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_reload_config(self, mock_file, mock_exists, manager, sample_python_config):
        """测试重新加载配置"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(sample_python_config)
        
        # 首次加载
        config1 = manager.load_config(Language.PYTHON)
        
        # 清除缓存并重新加载
        manager._config_cache.clear()
        config2 = manager.load_config(Language.PYTHON)
        
        # 配置内容应该相同，但不是同一个对象（因为重新加载了）
        assert config1 == config2
        assert config1 is not config2
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_syscall_count(self, mock_file, mock_exists, manager, sample_python_config):
        """测试获取系统调用数量"""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(sample_python_config)
        
        count = manager.get_syscall_count(Language.PYTHON)
        
        assert count == len(sample_python_config["allowedSyscalls"])
        assert count > 0
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_common_syscalls(self, mock_file, mock_exists, manager, sample_python_config, sample_nodejs_config):
        """测试获取通用系统调用"""
        mock_exists.return_value = True
        
        def mock_read_side_effect():
            # 根据调用次数返回不同的配置
            if mock_file.call_count <= 1:
                return json.dumps(sample_python_config)
            else:
                return json.dumps(sample_nodejs_config)
        
        mock_file.return_value.read.side_effect = mock_read_side_effect
        
        common_syscalls = manager.get_common_syscalls([Language.PYTHON, Language.NODEJS])
        
        assert isinstance(common_syscalls, list)
        # 通用系统调用应该在两个配置中都存在
        for syscall in common_syscalls:
            assert syscall in sample_python_config["allowedSyscalls"]
            assert syscall in sample_nodejs_config["allowedSyscalls"]
    
    @pytest.mark.unit
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_language_specific_syscalls(self, mock_file, mock_exists, manager, sample_python_config, sample_nodejs_config):
        """测试获取语言特定的系统调用"""
        mock_exists.return_value = True
        
        def mock_read_side_effect():
            if mock_file.call_count <= 1:
                return json.dumps(sample_python_config)
            else:
                return json.dumps(sample_nodejs_config)
        
        mock_file.return_value.read.side_effect = mock_read_side_effect
        
        python_specific = manager.get_language_specific_syscalls(Language.PYTHON, [Language.NODEJS])
        
        assert isinstance(python_specific, list)
        # Python特定的系统调用应该在Python中存在，但不在Node.js中
        for syscall in python_specific:
            assert syscall in sample_python_config["allowedSyscalls"]
            assert syscall not in sample_nodejs_config["allowedSyscalls"]