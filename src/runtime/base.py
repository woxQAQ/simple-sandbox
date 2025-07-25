from abc import ABC, abstractmethod
from typing import Dict, List

from .models import ExecutionResult, ResourceLimits


class LanguageRuntime(ABC):
    """语言运行时抽象基类"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(
        self,
        code: str,
        timeout: int,
        memory_limit: int,
        input_data: str = "",
        env_vars: Dict[str, str] | None = None,
    ) -> ExecutionResult:
        """执行给定的代码"""
        pass

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """返回支持的文件扩展名列表"""
        pass

    @abstractmethod
    def get_default_filename(self) -> str:
        """返回默认文件名"""
        pass

    def get_resource_limits(self) -> ResourceLimits:
        """获取资源限制配置"""
        return ResourceLimits()

    def preprocess_code(self, code: str) -> str:
        """预处理代码（用于特殊处理，如matplotlib）"""
        return code

    def get_command(self, filename: str) -> List[str]:
        """获取执行命令"""
        raise NotImplementedError
