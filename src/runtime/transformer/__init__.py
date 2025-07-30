"""
语言原生的AST插件系统
每个语言使用其原生AST解析器
"""

from .python.transformer import (
    PythonASTContext,
    PythonASTPlugin,
    PythonASTTransformer,
)

__all__ = ["PythonASTContext", "PythonASTPlugin", "PythonASTTransformer"]
