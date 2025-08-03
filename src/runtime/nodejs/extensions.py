"""
Node.js扩展系统（已移除transformer功能）
仅保留基本结构以确保兼容性
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class NodeJSASTManager:
    """Node.js AST管理器（已移除transformer功能）"""

    def __init__(self):
        pass

    def transform_code(
        self, code: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """直接返回原始代码，不再进行AST转换"""
        if context is None:
            context = {}

        # 直接返回原始代码，不再使用AST转换
        return code


# 全局管理器
nodejs_ast_manager = NodeJSASTManager()
