from typing import List, Dict, Any
from .base import LanguagePlugin
from .nodejs_transformers import (
    NodeJSConsoleTransformer,
)


class NodeJSPlugin(LanguagePlugin):
    """Node.js语言插件"""
    
    def __init__(self):
        super().__init__("nodejs")
        self._register_transformers()
    
    def _register_transformers(self):
        """注册Node.js转换器"""
        transformers = [
            NodeJSConsoleTransformer(),
        ]
        
        for transformer in transformers:
            self.register_transformer(transformer)
    
    def get_supported_extensions(self) -> List[str]:
        return [".js", ".mjs", ".cjs"]
    
    def get_default_filename(self) -> str:
        return "main.js"


# 创建Node.js插件实例
nodejs_plugin = NodeJSPlugin()