from typing import Dict, Any, Optional
from .base import CodeProcessor, ProcessingContext
from .handlers import (
    MatplotlibHandler,
    InputHandler,
    PandasHandler,
    SeabornHandler,
    NumpyHandler
)
import json
import os
from pathlib import Path


class PluginManager:
    """插件管理器 - 管理所有库处理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.processor = CodeProcessor()
        self.config_path = config_path
        self._load_default_handlers()
        self._load_config_handlers()
    
    def _load_default_handlers(self):
        """加载默认处理器"""
        default_handlers = [
            InputHandler(),
            MatplotlibHandler(),
            SeabornHandler(),
            PandasHandler(),
            NumpyHandler()
        ]
        
        for handler in default_handlers:
            self.processor.register_handler(handler)
    
    def _load_config_handlers(self):
        """从配置文件加载处理器"""
        if not self.config_path:
            # 使用默认配置路径
            config_path = Path(__file__).parent / "config" / "handlers.json"
            if config_path.exists():
                self.config_path = str(config_path)
        
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self._apply_config(config)
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def _apply_config(self, config: Dict[str, Any]):
        """应用配置"""
        handlers_config = config.get("handlers", {})
        
        for handler_name, handler_config in handlers_config.items():
            if handler_config.get("enabled", True):
                # 如果处理器已注册，更新优先级
                if handler_name in self.processor.handlers:
                    self.processor.handlers[handler_name].priority = handler_config.get("priority", 100)
            else:
                # 禁用处理器
                self.processor.unregister_handler(handler_name)
    
    def process_code(self, code: str, language: str, input_data: str = "", 
                     env_vars: Optional[Dict[str, Any]] = None) -> str:
        """处理代码"""
        context = ProcessingContext(language, input_data, env_vars)
        return self.processor.process_code(code, context)
    
    def get_available_handlers(self) -> Dict[str, Dict[str, Any]]:
        """获取可用处理器信息"""
        return self.processor.get_enabled_handlers()
    
    def register_custom_handler(self, handler):
        """注册自定义处理器"""
        self.processor.register_handler(handler)
    
    def unregister_handler(self, name: str):
        """注销处理器"""
        self.processor.unregister_handler(name)


# 全局插件管理器实例
plugin_manager = PluginManager()