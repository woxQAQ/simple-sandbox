"""
语言原生的AST插件系统
每个语言使用其原生AST解析器
"""

from .python_ast_plugin import PythonASTPlugin, PythonASTRegistry
from .nodejs_ast_plugin import NodeJSASTPlugin, NodeJSASTRegistry

__all__ = [
    "PythonASTPlugin",
    "PythonASTRegistry",
    "NodeJSASTPlugin",
    "NodeJSASTRegistry",
]
