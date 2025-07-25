from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ProcessingContext:
    """代码处理上下文"""
    
    def __init__(self, language: str, input_data: str = "", env_vars: Optional[Dict[str, str]] = None):
        self.language = language
        self.input_data = input_data
        self.env_vars = env_vars or {}
        self.metadata = {}


class LibraryHandler(ABC):
    """库处理器抽象基类"""
    
    def __init__(self, name: str, priority: int = 100):
        self.name = name
        self.priority = priority
    
    @abstractmethod
    def detect(self, code: str) -> bool:
        """检测代码是否包含需要处理的库"""
        pass
    
    @abstractmethod
    def process(self, code: str, context: ProcessingContext) -> str:
        """处理代码，返回处理后的代码"""
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """获取处理器配置"""
        return {
            "name": self.name,
            "priority": self.priority
        }


class CodeProcessor:
    """代码处理器管理器"""
    
    def __init__(self):
        self.handlers: Dict[str, LibraryHandler] = {}
        self._sorted_handlers = []
    
    def register_handler(self, handler: LibraryHandler):
        """注册处理器"""
        self.handlers[handler.name] = handler
        self._sort_handlers()
    
    def unregister_handler(self, name: str):
        """注销处理器"""
        if name in self.handlers:
            del self.handlers[name]
            self._sort_handlers()
    
    def _sort_handlers(self):
        """按优先级排序处理器"""
        self._sorted_handlers = sorted(
            self.handlers.values(),
            key=lambda h: h.priority,
            reverse=True
        )
    
    def process_code(self, code: str, context: ProcessingContext) -> str:
        """统一处理代码"""
        processed_code = code
        
        for handler in self._sorted_handlers:
            try:
                if handler.detect(processed_code):
                    processed_code = handler.process(processed_code, context)
            except Exception as e:
                # 记录错误但不中断处理
                print(f"Handler {handler.name} failed: {e}")
        
        return processed_code
    
    def get_enabled_handlers(self) -> Dict[str, Dict[str, Any]]:
        """获取启用的处理器信息"""
        return {
            name: handler.get_config()
            for name, handler in self.handlers.items()
        }