"""更新后的运行时seccomp注入器
使用统一的安全策略管理器
"""

import ctypes
import os
from typing import Dict

from security_manager import SecurityPolicyManager, SeccompLoader
from syscall_mapping import get_syscall_number

# 加载libseccomp
try:
    libseccomp = ctypes.CDLL("libseccomp.so.2")
    SECCOMP_AVAILABLE = True
except OSError:
    libseccomp = None
    SECCOMP_AVAILABLE = False


class UpdatedSeccompInjector:
    """使用统一安全策略管理器的seccomp注入器"""

    def __init__(self, bpf_dir: str = "build/seccomp"):
        self.security_manager = SecurityPolicyManager(bpf_dir)
        self.seccomp_loader = SeccompLoader()

        # 缓存已编译的BPF程序
        self.bpf_programs: Dict[str, bytes] = {}

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

    def _get_or_compile_bpf(self, language: str) -> bytes:
        """获取或编译指定语言的BPF字节码"""
        if language not in self.bpf_programs:
            try:
                bpf_bytes, _, _ = (
                    self.security_manager.generate_policy_for_language(language)
                )
                self.bpf_programs[language] = bpf_bytes
            except Exception as e:
                raise RuntimeError(f"Failed to compile BPF for {language}: {e}")

        return self.bpf_programs[language]

    def apply_policy(self, language: str, pid: int = None) -> bool:
        """应用seccomp策略到进程"""
        if pid is None:
            pid = os.getpid()

        # 验证语言支持
        if not self.security_manager.validate_language_support(language):
            print(f"Unsupported language: {language}")
            return False

        try:
            bpf_bytes = self._get_or_compile_bpf(language)
        except RuntimeError as e:
            print(f"Failed to get BPF program: {e}")
            return False

        if SECCOMP_AVAILABLE:
            return self._apply_with_libseccomp(language)
        else:
            return self._apply_with_prctl(bpf_bytes)

    def _apply_with_libseccomp(self, language: str) -> bool:
        """使用libseccomp应用策略"""
        try:
            # 获取系统调用列表
            syscalls = self.security_manager.load_syscalls_for_language(
                language
            )

            # 创建seccomp上下文
            ctx = self.libseccomp.seccomp_init(0)  # SCMP_ACT_KILL
            if not ctx:
                return False

            # 添加允许的syscall规则
            for syscall in syscalls:
                syscall_num = get_syscall_number(syscall)
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
                _fields_ = [
                    ("len", ctypes.c_ushort),
                    ("filter", ctypes.c_void_p),
                ]

            # 创建BPF程序数组
            bpf_array = (ctypes.c_char * len(bpf_bytes)).from_buffer_copy(
                bpf_bytes
            )

            # 创建sock_fprog
            prog = sock_fprog()
            prog.len = len(bpf_bytes) // 8  # 每个指令8字节
            prog.filter = ctypes.cast(bpf_array, ctypes.c_void_p)

            # 应用seccomp
            result = libc.prctl(
                PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ctypes.byref(prog)
            )

            return result == 0

        except Exception as e:
            print(f"Failed to apply seccomp with prctl: {e}")
            return False


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
