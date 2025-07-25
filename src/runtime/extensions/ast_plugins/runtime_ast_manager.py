"""
运行时AST管理器
协调各语言的AST转换
"""

import os
import json
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path

from .python_ast_plugin import python_ast_registry, PythonASTContext
from .nodejs_ast_plugin import nodejs_ast_registry


class RuntimeASTManager:
    """运行时AST转换管理器"""

    def __init__(self):
        self.language_handlers = {
            "python": self._transform_python,
            "javascript": self._transform_javascript,
            "typescript": self._transform_javascript,
            "nodejs": self._transform_javascript,
        }

    def transform_code(
        self, code: str, language: str, context: Dict[str, Any] = None
    ) -> str:
        """根据语言类型转换代码"""
        if context is None:
            context = {}

        handler = self.language_handlers.get(language)
        if not handler:
            return code

        try:
            return handler(code, context)
        except Exception as e:
            print(f"AST转换失败: {e}")
            return code

    def _transform_python(self, code: str, context: Dict[str, Any]) -> str:
        """转换Python代码"""
        try:
            ast_context = PythonASTContext(
                filename=context.get("filename", ""),
                source_code=code,
                user_id=context.get("user_id", ""),
                metadata=context,
            )
            return python_ast_registry.transform_code(code, ast_context)
        except Exception:
            return code

    def _transform_javascript(self, code: str, context: Dict[str, Any]) -> str:
        """转换JavaScript/TypeScript代码 - 通过Node进程调用acorn"""
        from .nodejs_ast_plugin import nodejs_ast_manager

        return nodejs_ast_manager.transform_code(code, context)

    def get_supported_languages(self) -> List[str]:
        """获取支持的语言"""
        return list(self.language_handlers.keys())

    def get_active_plugins(self, language: str) -> List[str]:
        """获取活跃插件"""
        if language == "python":
            return [plugin.name for plugin in python_ast_registry.plugins]
        elif language in ["javascript", "typescript", "nodejs"]:
            return [plugin.name for plugin in nodejs_ast_registry.plugins]
        return []


# 全局管理器
runtime_ast_manager = RuntimeASTManager()


def transform_ast_code(code: str, language: str, **context) -> str:
    """便捷函数转换代码"""
    return runtime_ast_manager.transform_code(code, language, context)


if __name__ == "__main__":
    # 测试
    test_python = """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

print("Creating plot...")
plt.plot(x, y)
plt.show()
"""

    test_js = """
console.log("Hello World");
const data = {key: "value"};
console.log(data);
"""

    print("=== Python AST转换 ===")
    transformed_python = transform_ast_code(test_python, "python")
    print(transformed_python)

    print("\n=== JavaScript AST转换 ===")
    transformed_js = transform_ast_code(test_js, "javascript")
    print(transformed_js)
