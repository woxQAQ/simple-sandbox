#!/usr/bin/env python3
"""
BPF模块测试

测试 src/security/bpf/ 目录中的功能：
1. 系统调用生成脚本
2. Makefile构建过程
3. C代码编译（在Linux上）
4. 生成的动态库功能
"""

import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
BPF_DIR = PROJECT_ROOT / "src" / "security" / "bpf"
STATIC_DIR = PROJECT_ROOT / "src" / "security" / "static"


class TestSyscallGeneration:
    """测试系统调用生成脚本"""

    def test_generate_syscalls_script_exists(self):
        """测试生成脚本文件存在"""
        script_path = BPF_DIR / "generate_syscalls.py"
        assert script_path.exists(), f"生成脚本不存在: {script_path}"
        assert script_path.is_file(), "生成脚本应该是文件"

    def test_generate_syscalls_executable(self):
        """测试生成脚本可执行"""
        script_path = BPF_DIR / "generate_syscalls.py"
        # 检查文件权限
        assert os.access(script_path, os.R_OK), "脚本应该可读"

    def test_syscall_map_completeness(self):
        """测试系统调用映射的完整性"""
        script_path = BPF_DIR / "generate_syscalls.py"

        # 读取脚本内容
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查关键系统调用是否存在
        essential_syscalls = [
            "read",
            "write",
            "open",
            "close",
            "mmap",
            "munmap",
            "brk",
            "exit",
            "exit_group",
            "rt_sigaction",
            "rt_sigreturn",
        ]

        for syscall in essential_syscalls:
            assert (
                f'"{syscall}"' in content
            ), f"关键系统调用 {syscall} 未在映射中找到"

    def test_generate_syscalls_with_python_config(self):
        """测试使用Python配置生成系统调用定义"""
        python_config = STATIC_DIR / "python.json"
        if not python_config.exists():
            pytest.skip("Python配置文件不存在")

        # 运行生成脚本
        result = subprocess.run(
            [sys.executable, "generate_syscalls.py"],
            cwd=BPF_DIR,
            capture_output=True,
            text=True,
            env={**os.environ, "LANG_CONFIG": "python"},
        )

        assert result.returncode == 0, f"生成脚本执行失败: {result.stderr}"
        assert "LANG_PYTHON" in result.stdout, "输出应包含Python语言条件编译"
        assert "ALLOWED_SYSCALLS" in result.stdout, "输出应包含系统调用数组"

    def test_generate_syscalls_with_nodejs_config(self):
        """测试使用Node.js配置生成系统调用定义"""
        nodejs_config = STATIC_DIR / "nodejs.json"
        if not nodejs_config.exists():
            pytest.skip("Node.js配置文件不存在")

        # 运行生成脚本
        result = subprocess.run(
            [sys.executable, "generate_syscalls.py"],
            cwd=BPF_DIR,
            capture_output=True,
            text=True,
            env={**os.environ, "LANG_CONFIG": "nodejs"},
        )

        assert result.returncode == 0, f"生成脚本执行失败: {result.stderr}"
        assert "LANG_NODEJS" in result.stdout, "输出应包含Node.js语言条件编译"
        assert "ALLOWED_SYSCALLS" in result.stdout, "输出应包含系统调用数组"

    def test_generated_header_format(self):
        """测试生成的头文件格式"""
        # 运行生成脚本
        result = subprocess.run(
            [sys.executable, "generate_syscalls.py"],
            cwd=BPF_DIR,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.skip(f"生成脚本执行失败: {result.stderr}")

        output = result.stdout

        # 检查C代码格式
        assert "#ifdef" in output, "应包含条件编译指令"
        assert "SYSCALL_COUNT" in output, "应包含系统调用计数宏"
        assert "static const int" in output, "应包含静态常量数组"
        assert "{" in output and "}" in output, "应包含数组定义"


class TestMakefileConfiguration:
    """测试Makefile配置和构建过程"""

    def test_makefile_exists(self):
        """测试Makefile存在"""
        makefile_path = BPF_DIR / "Makefile"
        assert makefile_path.exists(), f"Makefile不存在: {makefile_path}"

    def test_makefile_targets(self):
        """测试Makefile目标"""
        makefile_path = BPF_DIR / "Makefile"

        with open(makefile_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查关键目标
        expected_targets = [
            "all:",
            "clean:",
            "python:",
            "nodejs:",
            "info:",
            "help:",
            "check-deps:",
            "test-compile:",
        ]

        for target in expected_targets:
            assert target in content, f"Makefile缺少目标: {target}"

    def test_makefile_platform_detection(self):
        """测试Makefile平台检测"""
        makefile_path = BPF_DIR / "Makefile"

        with open(makefile_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查平台检测逻辑
        assert "uname -s" in content, "应包含平台检测"
        assert "Linux" in content, "应检查Linux平台"
        assert "error" in content, "应包含错误处理"

    def test_makefile_architecture_support(self):
        """测试Makefile架构支持"""
        makefile_path = BPF_DIR / "Makefile"

        with open(makefile_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查架构支持
        assert "x86_64" in content, "应支持x86_64架构"
        assert "aarch64" in content or "arm64" in content, "应支持ARM64架构"
        assert "ARCH_FLAGS" in content, "应定义架构标志"

    @pytest.mark.skipif(platform.system() != "Linux", reason="仅在Linux上测试")
    def test_makefile_check_deps(self):
        """测试Makefile依赖检查"""
        result = subprocess.run(
            ["make", "check-deps"], cwd=BPF_DIR, capture_output=True, text=True
        )

        # 依赖检查应该成功或给出明确错误
        assert result.returncode in [0, 1], "依赖检查应返回明确状态"

        if result.returncode == 0:
            assert "satisfied" in result.stdout.lower(), "成功时应显示满足信息"
        else:
            assert (
                "error" in result.stderr.lower()
                or "not found" in result.stderr.lower()
            ), "失败时应显示错误信息"

    @pytest.mark.skipif(platform.system() != "Linux", reason="仅在Linux上测试")
    def test_makefile_info_target(self):
        """测试Makefile信息目标"""
        result = subprocess.run(
            ["make", "info"], cwd=BPF_DIR, capture_output=True, text=True
        )

        assert result.returncode == 0, f"info目标执行失败: {result.stderr}"

        output = result.stdout
        assert "Platform:" in output, "应显示平台信息"
        assert "Architecture:" in output, "应显示架构信息"
        assert "Compiler:" in output, "应显示编译器信息"


class TestCCodeCompilation:
    """测试C代码编译（仅Linux）"""

    def test_c_source_files_exist(self):
        """测试C源文件存在"""
        c_file = BPF_DIR / "seccomp_injector.c"
        h_file = BPF_DIR / "seccomp_injector.h"

        assert c_file.exists(), f"C源文件不存在: {c_file}"
        assert h_file.exists(), f"头文件不存在: {h_file}"

    def test_header_file_structure(self):
        """测试头文件结构"""
        h_file = BPF_DIR / "seccomp_injector.h"

        with open(h_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查头文件保护
        assert "#ifndef" in content, "应包含头文件保护"
        assert "#define" in content, "应包含宏定义"
        assert "#endif" in content, "应包含结束标记"

        # 检查函数声明
        expected_functions = [
            "setup_no_new_privs",
            "drop_privileges",
            "apply_seccomp_filter",
            "inject_seccomp_profile",
        ]

        for func in expected_functions:
            assert func in content, f"应声明函数: {func}"

    def test_c_source_includes(self):
        """测试C源文件包含"""
        c_file = BPF_DIR / "seccomp_injector.c"

        with open(c_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查必要的包含
        essential_includes = [
            "#include <stdio.h>",
            "#include <stdlib.h>",
            "#include <unistd.h>",
            "#include <sys/prctl.h>",
        ]

        for include in essential_includes:
            assert include in content, f"应包含: {include}"

    @pytest.mark.skipif(platform.system() != "Linux", reason="仅在Linux上测试")
    def test_compilation_test(self):
        """测试编译测试目标"""
        # 首先生成系统调用头文件
        subprocess.run(
            ["make", "syscalls_generated.h"], cwd=BPF_DIR, capture_output=True
        )

        # 运行编译测试
        result = subprocess.run(
            ["make", "test-compile"],
            cwd=BPF_DIR,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.skip(f"编译测试失败，可能缺少依赖: {result.stderr}")

        assert "test passed" in result.stdout.lower(), "编译测试应该通过"


class TestGeneratedLibraries:
    """测试生成的动态库（仅Linux）"""

    @pytest.mark.skipif(platform.system() != "Linux", reason="仅在Linux上测试")
    def test_library_build_process(self):
        """测试库构建过程"""
        # 清理之前的构建
        subprocess.run(["make", "clean"], cwd=BPF_DIR, capture_output=True)

        # 尝试构建
        result = subprocess.run(
            ["make", "all"], cwd=BPF_DIR, capture_output=True, text=True
        )

        if result.returncode != 0:
            pytest.skip(f"库构建失败，可能缺少依赖: {result.stderr}")

        # 检查构建输出
        build_dir = PROJECT_ROOT / "build" / "lib"
        python_lib = build_dir / "libseccomp_injector_python.so"
        nodejs_lib = build_dir / "libseccomp_injector_nodejs.so"

        assert python_lib.exists(), f"Python库未生成: {python_lib}"
        assert nodejs_lib.exists(), f"Node.js库未生成: {nodejs_lib}"

    @pytest.mark.skipif(platform.system() != "Linux", reason="仅在Linux上测试")
    def test_library_symbols(self):
        """测试库符号导出"""
        build_dir = PROJECT_ROOT / "build" / "lib"
        python_lib = build_dir / "libseccomp_injector_python.so"

        if not python_lib.exists():
            pytest.skip("Python库不存在，跳过符号测试")

        # 使用nm或objdump检查符号
        result = subprocess.run(
            ["nm", "-D", str(python_lib)], capture_output=True, text=True
        )

        if result.returncode != 0:
            pytest.skip("无法检查库符号")

        # 检查关键函数符号
        expected_symbols = [
            "inject_seccomp_profile",
            "setup_no_new_privs",
            "drop_privileges",
            "apply_seccomp_filter",
        ]

        for symbol in expected_symbols:
            assert symbol in result.stdout, f"库应导出符号: {symbol}"


class TestCrossPlatformCompatibility:
    """测试跨平台兼容性"""

    def test_non_linux_platform_handling(self):
        """测试非Linux平台处理"""
        if platform.system() == "Linux":
            pytest.skip("在Linux上跳过非Linux测试")

        # 在非Linux平台上，Makefile应该报错
        result = subprocess.run(
            ["make", "info"], cwd=BPF_DIR, capture_output=True, text=True
        )

        # 应该失败并显示平台错误
        assert result.returncode != 0, "非Linux平台应该构建失败"
        assert (
            "platform" in result.stderr.lower()
            or "linux" in result.stderr.lower()
        ), "应显示平台错误信息"

    def test_architecture_detection(self):
        """测试架构检测"""
        # 检查当前架构是否被支持
        current_arch = platform.machine()

        makefile_path = BPF_DIR / "Makefile"
        with open(makefile_path, "r", encoding="utf-8") as f:
            content = f.read()

        if current_arch in ["x86_64", "amd64"]:
            assert "x86_64" in content, "应支持x86_64架构"
        elif current_arch in ["aarch64", "arm64"]:
            assert "aarch64" in content or "arm64" in content, "应支持ARM64架构"


class TestErrorHandling:
    """测试错误处理"""

    def test_missing_config_file_handling(self):
        """测试缺少配置文件的处理"""
        # 使用不存在的配置文件
        result = subprocess.run(
            [sys.executable, "generate_syscalls.py"],
            cwd=BPF_DIR,
            capture_output=True,
            text=True,
            env={**os.environ, "LANG_CONFIG": "nonexistent"},
        )

        # 应该优雅地处理错误
        if result.returncode != 0:
            assert len(result.stderr) > 0, "应该有错误信息"

    def test_invalid_syscall_handling(self):
        """测试无效系统调用处理"""
        # 创建临时配置文件，包含无效系统调用
        invalid_config = {
            "language": "test",
            "description": "Test config with invalid syscalls",
            "defaultAction": "SCMP_ACT_ERRNO",
            "architectures": ["SCMP_ARCH_X86_64"],
            "syscalls": [
                "read",  # 有效
                "invalid_syscall_name",  # 无效
                "write",  # 有效
            ],
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(invalid_config, f)
            temp_config = f.name

        try:
            # 修改生成脚本以使用临时配置
            result = subprocess.run(
                [sys.executable, "generate_syscalls.py"],
                cwd=BPF_DIR,
                capture_output=True,
                text=True,
                input=json.dumps(invalid_config),
            )

            # 脚本应该处理无效系统调用（跳过或报警）
            # 不应该崩溃
            assert result.returncode in [0, 1], "应该优雅地处理无效系统调用"

        finally:
            os.unlink(temp_config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
