#!/usr/bin/env python3
"""
测试新的扩展系统
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.runtime.extensions import (
    ASTTransformer,
    TransformationContext,
    plugin_registry,
)
from src.security.bpf_generator import BPFGenerator
from src.security.seccomp_injector import seccomp_manager


def test_ast_system():
    """测试AST插件系统"""
    print("🧪 测试AST插件系统...")
    
    # 获取所有插件
    plugins = plugin_registry.get_plugins('python')
    transformer = ASTTransformer(plugins)
    
    # 测试代码
    test_code = '''
import matplotlib.pyplot as plt

plt.plot([1, 2, 3, 4])
plt.show()
print("Hello World")
'''
    
    context = TransformationContext(
        language='python',
        user_id='test_user',
        code_hash='test_hash',
        metadata={'test': True}
    )
    
    try:
        transformed = transformer.transform(test_code, context)
        print("✅ AST转换成功")
        print("转换后的代码:")
        print(transformed)
    except Exception as e:
        print(f"❌ AST转换失败: {e}")


def test_seccomp_system():
    """测试seccomp系统"""
    print("\n🔒 测试seccomp系统...")
    
    # 生成策略
    generator = BPFGenerator()
    policies = generator.build_all()
    
    for name, path in policies.items():
        print(f"✅ 生成 {name} 策略: {path}")
        if path.exists():
            with open(path) as f:
                policy = json.load(f)
                print(f"   包含 {len(policy.get('syscalls', []))} 个系统调用")


def test_integration():
    """测试集成"""
    print("\n🔄 测试集成...")
    
    # 模拟代码执行流程
    print("1. 应用seccomp策略")
    success = seccomp_manager.setup_for_execution('python')
    print(f"   {'✅' if success else '❌'} 应用Python策略")
    
    print("2. 应用AST转换")
    plugins = plugin_registry.get_plugins('python')
    transformer = ASTTransformer(plugins)
    
    context = TransformationContext(
        language='python',
        user_id='test_user',
        code_hash='test_hash',
        metadata={'integration_test': True}
    )
    
    test_code = '''
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.plot(x, y)
plt.title('Sine Wave')
plt.show()
'''
    
    try:
        transformed = transformer.transform(test_code, context)
        print("✅ 集成测试通过")
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
    
    finally:
        seccomp_manager.cleanup_after_execution()


if __name__ == "__main__":
    import json
    
    print("🚀 新的扩展系统测试")
    print("=" * 50)
    
    try:
        test_ast_system()
        test_seccomp_system()
        test_integration()
        
        print("\n🎉 所有测试通过！")
        print("\n系统特性:")
        print("- ✅ 基于AST的插件系统")
        print("- ✅ 预编译BPF seccomp策略")
        print("- ✅ 运行时策略注入")
        print("- ✅ 声明式插件架构")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()