from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum


class ExecutionStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    MEMORY_EXCEEDED = "memory_exceeded"
    KILLED = "killed"


@dataclass
class ResourceLimits:
    max_memory_mb: int = 128
    max_cpu_time_seconds: int = 30
    max_processes: int = 5
    max_file_size_mb: int = 10
    max_files: int = 100


@dataclass
class ExecutionResult:
    status: ExecutionStatus
    stdout: str
    stderr: str
    execution_time: float
    memory_used_mb: float
    exit_code: Optional[int] = None
    error_message: Optional[str] = None


@dataclass
class ExecutionRequest:
    language: str
    code: str
    timeout: int = 30
    memory_limit: int = 128
    input_data: str = ""
    environment_variables: Dict[str, str] = None

    def __post_init__(self):
        if self.environment_variables is None:
            self.environment_variables = {}


class LanguageRuntime:
    """基础运行时接口"""
    
    def __init__(self, name: str):
        self.name = name
    
    def execute(self, code: str, timeout: int, memory_limit: int, 
                input_data: str = "", env_vars: Dict[str, str] = None) -> ExecutionResult:
        """执行代码并返回结果"""
        raise NotImplementedError
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        raise NotImplementedError
    
    def get_resource_limits(self) -> ResourceLimits:
        """获取运行时资源限制"""
        return ResourceLimits()
    
    def get_default_filename(self) -> str:
        """获取默认文件名"""
        raise NotImplementedError