from abc import ABC, abstractmethod
from typing import Dict, List

from src.models import ExecutionResult


class LanguageRuntime(ABC):
    """语言运行时抽象基类"""

    def __init__(self, name: str):
        self.name = name

    def get_language(self) -> str:
        """获取运行时语言名称"""
        return self.name

    @abstractmethod
    def execute(
        self,
        code: str,
        input_data: str = "",
        env_vars: dict[str, str] = {},
    ) -> ExecutionResult:
        """执行给定的代码"""
        pass

    def preprocess_code(self, code: str) -> str:
        """预处理代码（用于特殊处理，如matplotlib）"""
        return code
