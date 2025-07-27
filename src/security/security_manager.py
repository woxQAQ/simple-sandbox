"""统一的安全策略管理器
合并BPF编译和策略生成功能
"""

import ctypes
import json
import struct
from pathlib import Path
from typing import Dict, List, Tuple

from syscall_mapping import get_syscall_numbers


class SecurityPolicyManager:
    """统一的安全策略管理器"""

    # BPF指令常量
    BPF_LD = 0x00
    BPF_LDX = 0x01
    BPF_ST = 0x02
    BPF_STX = 0x03
    BPF_ALU = 0x04
    BPF_JMP = 0x05
    BPF_RET = 0x06
    BPF_MISC = 0x07

    # BPF大小
    BPF_W = 0x00
    BPF_H = 0x08
    BPF_B = 0x10

    # BPF模式
    BPF_IMM = 0x00
    BPF_ABS = 0x20
    BPF_IND = 0x40
    BPF_MEM = 0x60
    BPF_LEN = 0x80
    BPF_MSH = 0xA0

    # BPF操作符
    BPF_ADD = 0x00
    BPF_SUB = 0x10
    BPF_MUL = 0x20
    BPF_DIV = 0x30
    BPF_OR = 0x40
    BPF_AND = 0x50
    BPF_LSH = 0x60
    BPF_RSH = 0x70
    BPF_NEG = 0x80
    BPF_MOD = 0x90
    BPF_XOR = 0xA0

    # BPF跳转
    BPF_JA = 0x00
    BPF_JEQ = 0x10
    BPF_JGT = 0x20
    BPF_JGE = 0x30
    BPF_JSET = 0x40

    # BPF返回码
    BPF_K = 0x00
    BPF_X = 0x08

    def __init__(self, output_dir: str = "build/seccomp"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.syscalls_dir = Path(__file__).parent / "syscalls"

    def load_syscalls_for_language(self, language: str) -> List[str]:
        """加载指定语言的系统调用列表"""
        syscalls_file = self.syscalls_dir / f"{language}_syscalls.json"
        if not syscalls_file.exists():
            raise FileNotFoundError(f"Syscalls file not found: {syscalls_file}")

        with open(syscalls_file) as f:
            return json.load(f)

    def compile_syscalls_to_bpf(self, syscalls: List[str]) -> bytes:
        """将系统调用列表编译为BPF字节码"""
        # 获取系统调用号映射
        syscall_numbers = get_syscall_numbers(syscalls)

        if not syscall_numbers:
            raise ValueError("No valid syscalls found")

        # 生成BPF程序
        bpf_program = []

        # 加载系统调用号 (从seccomp_data结构的nr字段)
        bpf_program.append(
            self._create_instruction(
                self.BPF_LD | self.BPF_W | self.BPF_ABS, 0, 0, 0
            )
        )

        # 为每个允许的syscall添加检查
        for syscall_num in syscall_numbers:
            bpf_program.extend(self._create_syscall_check(syscall_num))

        # 默认拒绝
        bpf_program.append(
            self._create_instruction(
                self.BPF_RET | self.BPF_K,
                0,
                0,
                0,  # SECCOMP_RET_KILL
            )
        )

        return self._pack_bpf_program(bpf_program)

    def generate_policy_for_language(
        self, language: str
    ) -> Tuple[bytes, Path, Path]:
        """为指定语言生成完整的安全策略

        Returns:
            (BPF字节码, BPF文件路径, JSON配置文件路径)
        """
        # 加载系统调用列表
        syscalls = self.load_syscalls_for_language(language)

        # 编译BPF字节码
        bpf_bytes = self.compile_syscalls_to_bpf(syscalls)

        # 保存BPF字节码
        bpf_path = self.output_dir / f"{language}.bpf"
        with open(bpf_path, "wb") as f:
            f.write(bpf_bytes)

        # 生成JSON配置
        config = {
            "defaultAction": "SCMP_ACT_ERRNO",
            "architectures": ["SCMP_ARCH_X86_64"],
            "syscalls": [{"names": syscalls, "action": "SCMP_ACT_ALLOW"}],
        }

        config_path = self.output_dir / f"{language}.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        # 生成C数组格式（用于静态链接）
        self._generate_c_array(language, bpf_bytes)

        return bpf_bytes, bpf_path, config_path

    def generate_all_policies(self) -> Dict[str, Tuple[bytes, Path, Path]]:
        """生成所有支持语言的安全策略"""
        results = {}

        # 扫描syscalls目录找到所有支持的语言
        for syscalls_file in self.syscalls_dir.glob("*_syscalls.json"):
            language = syscalls_file.stem.replace("_syscalls", "")
            try:
                results[language] = self.generate_policy_for_language(language)
                print(f"✅ Generated {language} security policy")
            except Exception as e:
                print(f"❌ Failed to generate {language} policy: {e}")

        return results

    def _create_instruction(self, code: int, jt: int, jf: int, k: int) -> bytes:
        """创建BPF指令"""
        return struct.pack("HBBI", code & 0xFFFF, jt, jf, k)

    def _create_syscall_check(self, syscall_num: int) -> List[bytes]:
        """创建系统调用检查指令"""
        instructions = []

        # 检查是否等于这个系统调用号
        instructions.append(
            self._create_instruction(
                self.BPF_JMP | self.BPF_JEQ | self.BPF_K, 0, 1, syscall_num
            )
        )

        # 如果匹配，允许
        instructions.append(
            self._create_instruction(
                self.BPF_RET | self.BPF_K,
                0,
                0,
                0x7FFF0000,  # SECCOMP_RET_ALLOW
            )
        )

        return instructions

    def _pack_bpf_program(self, instructions: List[bytes]) -> bytes:
        """打包BPF程序"""
        return b"".join(instructions)

    def _generate_c_array(self, language: str, bpf_bytes: bytes) -> Path:
        """生成C数组格式的BPF程序"""
        c_array = ", ".join(f"0x{b:02x}" for b in bpf_bytes)
        c_path = self.output_dir / f"{language}_bpf.c"

        c_content = f"""/* Auto-generated BPF program for {language} */
#include <stddef.h>

const unsigned char {language}_bpf[] = {{
    {c_array}
}};

const size_t {language}_bpf_len = {len(bpf_bytes)};
"""

        with open(c_path, "w") as f:
            f.write(c_content)

        return c_path

    def validate_language_support(self, language: str) -> bool:
        """验证是否支持指定语言"""
        syscalls_file = self.syscalls_dir / f"{language}_syscalls.json"
        return syscalls_file.exists()

    def get_supported_languages(self) -> List[str]:
        """获取所有支持的语言列表"""
        languages = []
        for syscalls_file in self.syscalls_dir.glob("*_syscalls.json"):
            language = syscalls_file.stem.replace("_syscalls", "")
            languages.append(language)
        return sorted(languages)


class SeccompLoader:
    """seccomp动态链接加载器"""

    def __init__(self):
        try:
            self.libc = ctypes.CDLL("libc.so.6")
            self.libseccomp = ctypes.CDLL("libseccomp.so.2")
            self.available = True
        except OSError:
            self.libc = None
            self.libseccomp = None
            self.available = False

    def load_bpf_program(self, bpf_bytes: bytes, pid: int = None) -> bool:
        """加载BPF程序到进程"""
        if not self.available:
            print("Warning: libseccomp not available")
            return False

        import os

        if pid is None:
            pid = os.getpid()

        try:
            # 使用prctl系统调用应用BPF字节码
            return self._apply_with_prctl(bpf_bytes)
        except Exception as e:
            print(f"Failed to load BPF program: {e}")
            return False

    def _apply_with_prctl(self, bpf_bytes: bytes) -> bool:
        """使用prctl系统调用应用BPF字节码"""
        try:
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
            result = self.libc.prctl(
                PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ctypes.byref(prog)
            )

            return result == 0

        except Exception as e:
            print(f"Failed to apply seccomp with prctl: {e}")
            return False


if __name__ == "__main__":
    """测试安全策略管理器"""
    print("🧪 测试安全策略管理器...")

    manager = SecurityPolicyManager()

    # 显示支持的语言
    languages = manager.get_supported_languages()
    print(f"📋 支持的语言: {', '.join(languages)}")

    # 生成所有策略
    results = manager.generate_all_policies()

    for language, (bpf_bytes, bpf_path, config_path) in results.items():
        print(f"✅ {language}: {len(bpf_bytes)} bytes BPF, saved to {bpf_path}")

    # 测试加载器
    loader = SeccompLoader()
    if loader.available:
        print("✅ Seccomp loader available")
    else:
        print("⚠️  Seccomp loader not available (libseccomp missing)")
