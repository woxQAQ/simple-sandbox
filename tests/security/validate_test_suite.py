#!/usr/bin/env python3
"""
安全模块测试套件验证脚本

此脚本验证整个安全模块测试套件的完整性和正确性，包括：
1. 测试文件存在性检查
2. 测试覆盖率分析
3. 平台兼容性验证
4. GitHub Actions工作流验证
5. BPF模块测试验证
"""

import platform
import subprocess
import sys
from pathlib import Path

import yaml

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
SECURITY_DIR = PROJECT_ROOT / "src" / "security"
TESTS_DIR = PROJECT_ROOT / "tests" / "security"
WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"


class TestSuiteValidator:
    """测试套件验证器"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed_checks = []

    def log_error(self, message: str):
        """记录错误"""
        self.errors.append(f"❌ {message}")
        print(f"❌ {message}")

    def log_warning(self, message: str):
        """记录警告"""
        self.warnings.append(f"⚠️  {message}")
        print(f"⚠️  {message}")

    def log_success(self, message: str):
        """记录成功"""
        self.passed_checks.append(f"✅ {message}")
        print(f"✅ {message}")

    def check_test_files_exist(self) -> bool:
        """检查测试文件是否存在"""
        print("\n🔍 检查测试文件存在性...")

        required_files = [
            "test_security_integration.py",
            "test_security_manager.py",
            "test_security_errors.py",
            "test_security_performance.py",
            "test_security_cross_platform.py",
            "test_bpf_module.py",
            "test_seccomp_injector.py",
            "run_tests.py",
        ]

        all_exist = True
        for file in required_files:
            file_path = TESTS_DIR / file
            if file_path.exists():
                self.log_success(f"测试文件存在: {file}")
            else:
                self.log_error(f"测试文件缺失: {file}")
                all_exist = False

        return all_exist

    def check_source_files_exist(self) -> bool:
        """检查源文件是否存在"""
        print("\n🔍 检查源文件存在性...")

        required_files = [
            "__init__.py",
            "injection/seccomp_wrapper.py",
            "bpf/Makefile",
            "bpf/seccomp_injector.h",
            "bpf/seccomp_injector.c",
            "bpf/generate_syscalls.py",
            "static/python.json",
            "static/nodejs.json",
        ]

        all_exist = True
        for file in required_files:
            file_path = SECURITY_DIR / file
            if file_path.exists():
                self.log_success(f"源文件存在: {file}")
            else:
                self.log_error(f"源文件缺失: {file}")
                all_exist = False

        return all_exist

    def validate_github_workflows(self) -> bool:
        """验证GitHub Actions工作流"""
        print("\n🔍 验证GitHub Actions工作流...")

        workflows = ["security-tests.yml", "bpf-build.yml"]

        all_valid = True
        for workflow in workflows:
            workflow_path = WORKFLOWS_DIR / workflow
            if not workflow_path.exists():
                self.log_error(f"工作流文件缺失: {workflow}")
                all_valid = False
                continue

            try:
                with open(workflow_path, "r", encoding="utf-8") as f:
                    yaml.safe_load(f)
                self.log_success(f"工作流语法正确: {workflow}")
            except yaml.YAMLError as e:
                self.log_error(f"工作流语法错误 {workflow}: {e}")
                all_valid = False

        return all_valid

    def run_cross_platform_tests(self) -> bool:
        """运行跨平台测试"""
        print("\n🔍 运行跨平台测试...")

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/security/test_security_cross_platform.py",
                    "-v",
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                self.log_success("跨平台测试通过")
                return True
            else:
                self.log_error(f"跨平台测试失败: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            self.log_error("跨平台测试超时")
            return False
        except Exception as e:
            self.log_error(f"跨平台测试执行错误: {e}")
            return False

    def run_bpf_tests(self) -> bool:
        """运行BPF模块测试"""
        print("\n🔍 运行BPF模块测试...")

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/security/test_bpf_module.py",
                    "-v",
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                self.log_success("BPF模块测试通过")
                return True
            else:
                self.log_error(f"BPF模块测试失败: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            self.log_error("BPF模块测试超时")
            return False
        except Exception as e:
            self.log_error(f"BPF模块测试执行错误: {e}")
            return False

    def check_platform_compatibility(self) -> bool:
        """检查平台兼容性"""
        print("\n🔍 检查平台兼容性...")

        current_platform = platform.system()
        self.log_success(f"当前平台: {current_platform}")

        if current_platform == "Linux":
            self.log_success("Linux平台支持完整功能")
            # 在Linux上可以测试seccomp功能
            return True
        else:
            self.log_warning(f"{current_platform}平台仅支持跨平台功能")
            # 非Linux平台只能测试跨平台功能
            return True

    def generate_coverage_report(self) -> bool:
        """生成测试覆盖率报告"""
        print("\n🔍 生成测试覆盖率报告...")

        try:
            # 运行带覆盖率的测试
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/security/",
                    "--cov=src/security",
                    "--cov-report=term-missing",
                    "--cov-report=html",
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                self.log_success("测试覆盖率报告生成成功")
                # 解析覆盖率
                if "TOTAL" in result.stdout:
                    lines = result.stdout.split("\n")
                    for line in lines:
                        if "TOTAL" in line:
                            self.log_success(f"总体覆盖率: {line.strip()}")
                            break
                return True
            else:
                self.log_warning(f"覆盖率报告生成失败: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            self.log_warning("覆盖率报告生成超时")
            return False
        except Exception as e:
            self.log_warning(f"覆盖率报告生成错误: {e}")
            return False

    def validate_test_suite(self) -> bool:
        """验证整个测试套件"""
        print("🚀 开始验证安全模块测试套件...")

        checks = [
            self.check_test_files_exist,
            self.check_source_files_exist,
            self.validate_github_workflows,
            self.check_platform_compatibility,
            self.run_cross_platform_tests,
            self.run_bpf_tests,
            self.generate_coverage_report,
        ]

        all_passed = True
        for check in checks:
            try:
                if not check():
                    all_passed = False
            except Exception as e:
                self.log_error(f"检查执行错误: {e}")
                all_passed = False

        return all_passed

    def print_summary(self):
        """打印验证摘要"""
        print("\n" + "=" * 60)
        print("📊 测试套件验证摘要")
        print("=" * 60)

        print(f"\n✅ 通过检查: {len(self.passed_checks)}")
        for check in self.passed_checks:
            print(f"  {check}")

        if self.warnings:
            print(f"\n⚠️  警告: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  {warning}")

        if self.errors:
            print(f"\n❌ 错误: {len(self.errors)}")
            for error in self.errors:
                print(f"  {error}")

        if not self.errors:
            print("\n🎉 测试套件验证完成，所有关键检查都通过！")
        else:
            print("\n💥 测试套件验证失败，请修复上述错误。")


def main():
    """主函数"""
    validator = TestSuiteValidator()

    success = validator.validate_test_suite()
    validator.print_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
