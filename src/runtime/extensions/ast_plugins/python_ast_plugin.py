"""
Python原生AST插件系统
使用Python内置ast模块
"""

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .py_plugins.console_plugin import PythonConsoleASTPlugin
from .py_plugins.matplotlib_plugin import MatplotlibASTPlugin


@dataclass
class PythonASTContext:
    """Python AST转换上下文"""

    filename: str
    source_code: str
    user_id: str
    metadata: Dict[str, Any]


class PythonASTPlugin(ABC):
    """Python AST插件基类"""

    def __init__(self, name: str, priority: int = 100):
        self.name = name
        self.priority = priority

    @abstractmethod
    def should_transform(self, node: ast.AST, context: PythonASTContext) -> bool:
        """判断是否应该应用此插件"""
        pass

    @abstractmethod
    def transform(self, node: ast.AST, context: PythonASTContext) -> ast.AST:
        """转换AST节点"""
        pass

    def visit(self, tree: ast.AST, context: PythonASTContext) -> ast.AST:
        """访问并转换整个AST树"""
        return self._visit_recursive(tree, context)

    def _visit_recursive(self, node: ast.AST, context: PythonASTContext) -> ast.AST:
        """递归访问AST节点"""
        if self.should_transform(node, context):
            node = self.transform(node, context)

        # 递归处理子节点
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, ast.AST):
                        new_item = self._visit_recursive(item, context)
                        new_list.append(new_item)
                    else:
                        new_list.append(item)
                setattr(node, field, new_list)
            elif isinstance(value, ast.AST):
                new_value = self._visit_recursive(value, context)
                setattr(node, field, new_value)

        return node


class PythonASTTransformer(ast.NodeTransformer):
    """Python AST转换器"""

    def __init__(self, plugins: List[PythonASTPlugin]):
        self.plugins = sorted(plugins, key=lambda p: p.priority)
        self.context: Optional[PythonASTContext] = None

    def transform(self, code: str, context: PythonASTContext) -> str:
        """转换代码"""
        self.context = context

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code  # 语法错误时返回原代码

        # 应用所有插件
        for plugin in self.plugins:
            tree = plugin.visit(tree, context)

        # 生成代码
        import astor

        return astor.to_source(tree)


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
