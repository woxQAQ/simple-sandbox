"""
运行时AST管理器
协调各语言的AST转换
"""

import logging
from typing import Any, Dict

from src.runtime.python.extensions import python_ast_registry
from src.runtime.python.transformer import PythonASTContext

logger = logging.getLogger(__name__)


class RuntimeASTManager:
    """运行时AST转换管理器"""

    def __init__(self):
        self.language_handlers = {
            "python": self._transform_python,
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
            logger.warning(f"AST转换失败: {e}")
            return code

    def _transform_python(self, code: str, context: Dict[str, Any]) -> str:
        """转换Python代码"""
        try:
            ast_context = PythonASTContext(
                source_code=code,
            )
            return python_ast_registry.transform_code(code, ast_context)
        except Exception:
            return code

    def _transform_javascript(self, code: str, context: Dict[str, Any]) -> str:
        """转换JavaScript/TypeScript代码 - Node.js transformer已移除，直接返回原代码"""
        # Node.js transformer已被移除，直接返回原始代码
        return code


# 全局管理器
runtime_ast_manager = RuntimeASTManager()


def transform_ast_code(code: str, language: str, **context) -> str:
    """便捷函数转换代码"""
    return runtime_ast_manager.transform_code(code, language, context)
