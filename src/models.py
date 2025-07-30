"""
公共数据模型定义
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ExecutionStatus(Enum):
    """执行状态枚举"""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    KILLED = "killed"


@dataclass
class ExecutionRequest:
    """执行请求"""

    language: str
    code: str
    input_data: str = ""
    env_vars: Optional[Dict[str, str]] = None
    timeout: Optional[float] = None
    
    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}


@dataclass
class ExecutionResult:
    """执行结果"""

    status: ExecutionStatus
    stdout: str
    stderr: str
    execution_time: float
    memory_used_mb: float
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
