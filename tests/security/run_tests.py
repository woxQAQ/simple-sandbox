#!/usr/bin/env python3
"""
安全模块测试运行器

这个脚本会根据当前平台自动选择合适的测试来运行：
- Linux: 运行完整的集成测试
- 其他平台: 运行跨平台兼容的测试
"""

import sys
import platform
import subprocess
from pathlib import Path


def get_test_directory():
    """获取测试目录路径"""
    return Path(__file__).parent


def is_linux():
    """检查是否为Linux平台"""
    return platform.system().lower() == "linux"


def run_tests(test_files, verbose=True):
    """运行指定的测试文件"""
    test_dir = get_test_directory()

    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")

    # 添加测试文件
    for test_file in test_files:
        cmd.append(str(test_dir / test_file))

    print(f"运行命令: {' '.join(cmd)}")
    print(f"当前平台: {platform.system()}")
    print("=" * 50)

    try:
        result = subprocess.run(cmd, cwd=test_dir.parent.parent)
        return result.returncode
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return 1


def main():
    """主函数"""
    print("安全模块测试运行器")
    print("=" * 50)

    if is_linux():
        print("检测到Linux平台，运行完整的集成测试...")
        test_files = [
            "test_security_integration.py",
            "test_security_manager.py",
            "test_seccomp_injector.py",
            "test_security_errors.py",
            "test_security_performance.py",
            "test_security_cross_platform.py",
        ]
    else:
        print(f"检测到{platform.system()}平台，运行跨平台兼容测试...")
        test_files = ["test_security_cross_platform.py"]

    return_code = run_tests(test_files)

    if return_code == 0:
        print("\n✅ 所有测试通过！")
    else:
        print(f"\n❌ 测试失败，退出码: {return_code}")

    return return_code


if __name__ == "__main__":
    sys.exit(main())
