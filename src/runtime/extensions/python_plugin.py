from typing import List, Dict, Any
from .base import LanguagePlugin
from .python_transformers import (
    PythonMatplotlibTransformer,
)


class PythonPlugin(LanguagePlugin):
    """Python语言插件"""
    
    def __init__(self):
        super().__init__("python")
        self._register_transformers()
    
    def _register_transformers(self):
        """注册Python转换器"""
        transformers = [
            PythonMatplotlibTransformer(),
        ]
        
        for transformer in transformers:
            self.register_transformer(transformer)
    
    def get_supported_extensions(self) -> List[str]:
        return [".py", ".pyw"]
    
    def get_default_filename(self) -> str:
        return "main.py"


# 创建Python插件实例
python_plugin = PythonPlugin()