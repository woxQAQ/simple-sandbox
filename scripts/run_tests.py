#!/usr/bin/env python3
"""
测试运行脚本
提供便捷的测试运行命令和选项
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> int:
    """运行命令并返回退出码"""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"运行命令时出错: {e}")
        return 1


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def check_dependencies() -> bool:
    """检查依赖是否安装"""
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: 未找到 uv 包管理器，请先安装 uv")
        print("安装命令: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False


def install_dependencies() -> int:
    """安装依赖"""
    print("安装项目依赖...")
    return run_command(["uv", "sync", "--dev"])


def run_unit_tests(verbose: bool = False, coverage: bool = True) -> int:
    """运行单元测试"""
    cmd = ["uv", "run", "pytest", "tests/unit/"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing"])

    cmd.extend(["-m", "unit"])

    return run_command(cmd)


def run_integration_tests(verbose: bool = False) -> int:
    """运行集成测试"""
    cmd = ["uv", "run", "pytest", "tests/integration/"]

    if verbose:
        cmd.append("-v")

    cmd.extend(["-m", "integration"])

    return run_command(cmd)


def run_e2e_tests(verbose: bool = False) -> int:
    """运行端到端测试"""
    cmd = ["uv", "run", "pytest", "tests/e2e/"]

    if verbose:
        cmd.append("-v")

    cmd.extend(["-m", "e2e"])

    return run_command(cmd)


def run_security_tests(verbose: bool = False) -> int:
    """运行安全测试"""
    cmd = ["uv", "run", "pytest", "tests/security/"]

    if verbose:
        cmd.append("-v")

    cmd.extend(["-m", "security"])

    return run_command(cmd)


def run_performance_tests(verbose: bool = False) -> int:
    """运行性能测试"""
    cmd = ["uv", "run", "pytest", "tests/performance/"]

    if verbose:
        cmd.append("-v")

    cmd.extend(["-m", "performance", "--durations=0"])

    return run_command(cmd)


def run_all_tests(
    verbose: bool = False, coverage: bool = True, exclude_slow: bool = True
) -> int:
    """运行所有测试"""
    cmd = ["uv", "run", "pytest", "tests/"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(
            [
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml",
            ]
        )

    if exclude_slow:
        cmd.extend(["-m", "not slow"])

    return run_command(cmd)


def run_quick_tests(verbose: bool = False) -> int:
    """运行快速测试（单元测试 + 基本集成测试）"""
    cmd = ["uv", "run", "pytest", "tests/unit/", "tests/integration/"]

    if verbose:
        cmd.append("-v")

    cmd.extend(["--cov=src", "--cov-report=term-missing", "-m", "not slow"])

    return run_command(cmd)


def run_smoke_tests(verbose: bool = False) -> int:
    """运行冒烟测试"""
    cmd = ["uv", "run", "pytest", "tests/"]

    if verbose:
        cmd.append("-v")

    cmd.extend(["-m", "smoke"])

    return run_command(cmd)


def run_specific_test(test_path: str, verbose: bool = False) -> int:
    """运行特定测试"""
    cmd = ["uv", "run", "pytest", test_path]

    if verbose:
        cmd.append("-v")

    return run_command(cmd)


def run_linting() -> int:
    """运行代码检查"""
    print("运行代码格式检查...")

    # Ruff 检查
    ruff_check = run_command(["uv", "run", "ruff", "check", "src", "tests"])

    # Ruff 格式检查
    ruff_format = run_command(
        ["uv", "run", "ruff", "format", "--check", "src", "tests"]
    )

    # MyPy 类型检查
    mypy_check = run_command(["uv", "run", "mypy", "src"])

    return max(ruff_check, ruff_format, mypy_check)


def run_security_scan() -> int:
    """运行安全扫描"""
    print("运行安全扫描...")

    # Bandit 安全扫描
    bandit_result = run_command(["uv", "run", "bandit", "-r", "src/"])

    # Safety 依赖安全检查
    safety_result = run_command(["uv", "run", "safety", "check"])

    return max(bandit_result, safety_result)


def generate_coverage_report() -> int:
    """生成覆盖率报告"""
    print("生成覆盖率报告...")

    # 运行测试并生成覆盖率
    test_result = run_command(
        [
            "uv",
            "run",
            "pytest",
            "tests/",
            "--cov=src",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cov-report=term-missing",
            "-m",
            "not slow",
        ]
    )

    if test_result == 0:
        print("\n覆盖率报告已生成:")
        print("  HTML报告: htmlcov/index.html")
        print("  XML报告: coverage.xml")

    return test_result


def clean_test_artifacts() -> int:
    """清理测试产物"""
    print("清理测试产物...")

    artifacts = [
        ".pytest_cache",
        "htmlcov",
        "coverage.xml",
        "tests.log",
        ".coverage",
        "bandit-report.json",
        "safety-report.json",
    ]

    project_root = get_project_root()

    for artifact in artifacts:
        artifact_path = project_root / artifact
        if artifact_path.exists():
            if artifact_path.is_dir():
                import shutil

                shutil.rmtree(artifact_path)
                print(f"删除目录: {artifact}")
            else:
                artifact_path.unlink()
                print(f"删除文件: {artifact}")

    print("清理完成")
    return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Simple Sandbox 测试运行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s unit                    # 运行单元测试
  %(prog)s integration             # 运行集成测试
  %(prog)s all                     # 运行所有测试
  %(prog)s quick                   # 运行快速测试
  %(prog)s specific tests/unit/api/test_models.py  # 运行特定测试
  %(prog)s lint                    # 运行代码检查
  %(prog)s security-scan           # 运行安全扫描
  %(prog)s coverage                # 生成覆盖率报告
  %(prog)s clean                   # 清理测试产物
""",
    )

    parser.add_argument(
        "command",
        choices=[
            "unit",
            "integration",
            "e2e",
            "security",
            "performance",
            "all",
            "quick",
            "smoke",
            "specific",
            "lint",
            "security-scan",
            "coverage",
            "clean",
            "install",
        ],
        help="要执行的测试类型或操作",
    )

    parser.add_argument(
        "test_path", nargs="?", help="特定测试路径（仅用于 specific 命令）"
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")

    parser.add_argument(
        "--no-coverage", action="store_true", help="禁用覆盖率检查"
    )

    parser.add_argument(
        "--include-slow", action="store_true", help="包含慢速测试"
    )

    args = parser.parse_args()

    # 检查依赖
    if args.command != "clean" and not check_dependencies():
        return 1

    # 切换到项目根目录
    os.chdir(get_project_root())

    # 执行命令
    if args.command == "install":
        return install_dependencies()
    elif args.command == "unit":
        return run_unit_tests(args.verbose, not args.no_coverage)
    elif args.command == "integration":
        return run_integration_tests(args.verbose)
    elif args.command == "e2e":
        return run_e2e_tests(args.verbose)
    elif args.command == "security":
        return run_security_tests(args.verbose)
    elif args.command == "performance":
        return run_performance_tests(args.verbose)
    elif args.command == "all":
        return run_all_tests(
            args.verbose, not args.no_coverage, not args.include_slow
        )
    elif args.command == "quick":
        return run_quick_tests(args.verbose)
    elif args.command == "smoke":
        return run_smoke_tests(args.verbose)
    elif args.command == "specific":
        if not args.test_path:
            print("错误: specific 命令需要指定测试路径")
            return 1
        return run_specific_test(args.test_path, args.verbose)
    elif args.command == "lint":
        return run_linting()
    elif args.command == "security-scan":
        return run_security_scan()
    elif args.command == "coverage":
        return generate_coverage_report()
    elif args.command == "clean":
        return clean_test_artifacts()
    else:
        print(f"未知命令: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
