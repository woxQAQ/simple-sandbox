#!/usr/bin/env python3
"""
构建脚本
生成预编译的BPF seccomp策略
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.security.bpf_generator import BPFGenerator


def main():
    """主构建函数"""
    print("🔧 构建预编译seccomp策略...")

    # 创建构建目录
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)

    # 生成BPF策略
    generator = BPFGenerator()
    policies = generator.build_all()

    for name, path in policies.items():
        print(f"✅ 生成 {name} 策略: {path}")

    print("🎉 构建完成！")


if __name__ == "__main__":
    main()
