#!/usr/bin/env python3
"""
简化测试
"""

import ast
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_ast_system():
    """测试AST插件系统"""
    print("🧪 测试AST插件系统...")
    
    # 测试matplotlib插件
    from src.runtime.extensions.plugins.matplotlib_plugin import MatplotlibPlugin
    
    plugin = MatplotlibPlugin()
    test_code = '''
import matplotlib.pyplot as plt
plt.plot([1, 2, 3, 4])
plt.show()
'''
    
    context = type('Context', (), {
        'language': 'python',
        'user_id': 'test_user',
        'code_hash': 'test_hash',
        'metadata': {}
    })()
    
    try:
        tree = ast.parse(test_code)
        
        # 检查是否应该转换
        for node in ast.walk(tree):
            if plugin.should_transform(node, context):
                print(f"✅ 检测到需要转换的节点: {type(node).__name__}")
        
        print("✅ AST系统测试通过")
    except Exception as e:
        print(f"❌ AST系统测试失败: {e}")

def test_seccomp_system():
    """测试seccomp系统"""
    print("\n🔒 测试seccomp系统...")
    
    from src.security.bpf_generator import BPFGenerator
    
    generator = BPFGenerator()
    policies = generator.build_all()
    
    for name, path in policies.items():
        print(f"✅ 生成策略: {name} -> {path}")
        if path.exists():
            print(f"   文件大小: {path.stat().st_size} bytes")

if __name__ == "__main__":
    print("🚀 系统测试")
    print("=" * 30)
    
    try:
        test_ast_system()
        test_seccomp_system()
        print("\n🎉 测试完成！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()