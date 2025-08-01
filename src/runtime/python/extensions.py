"""
Python原生AST插件系统
使用Python内置ast模块
"""

from typing import List

from src.runtime.python.plugins import (
    MatplotlibASTPlugin,
    PythonConsoleASTPlugin,
)
from src.runtime.python.transformer import (
    PythonASTContext,
    PythonASTPlugin,
    PythonASTTransformer,
)


class PythonASTRegistry:
    """Python AST插件注册表"""

    def __init__(self):
        self.plugins: List[PythonASTPlugin] = []

    def register(self, plugin: PythonASTPlugin):
        """注册插件"""
        self.plugins.append(plugin)
        # 按优先级排序
        self.plugins.sort(key=lambda p: p.priority, reverse=True)

    def transform_code(self, code: str, context: PythonASTContext) -> str:
        """转换Python代码"""
        if not self.plugins:
            return code

        transformer = PythonASTTransformer(self.plugins)
        return transformer.transform(code, context)


# 从py_plugins导入插件

# 全局注册表
python_ast_registry = PythonASTRegistry()

# 注册插件
python_ast_registry.register(PythonConsoleASTPlugin())
python_ast_registry.register(MatplotlibASTPlugin())
