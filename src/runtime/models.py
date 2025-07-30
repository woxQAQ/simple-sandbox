"""
运行时模型定义
"""

# 从公共模型导入以保持兼容性并避免循环导入
from src.models import (
    ExecutionStatus,
    ExecutionRequest,
    ExecutionResult,
)

# 保持向后兼容性
__all__ = [
    "ExecutionStatus",
    "ExecutionRequest", 
    "ExecutionResult",
]
