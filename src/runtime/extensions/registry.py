from typing import Dict, Any, List, Optional
from .base import PluginRegistry, TransformationContext
from .python_plugin import python_plugin
from .nodejs_plugin import nodejs_plugin


class ExtensionManager:
    """扩展管理器 - 管理所有语言扩展"""
    
    def __init__(self):
        self.registry = PluginRegistry()
        self._initialize_plugins()
    
    def _initialize_plugins(self):
        """初始化所有插件"""
        # 注册内置插件
        self.registry.register_plugin(python_plugin)
        self.registry.register_plugin(nodejs_plugin)
    
    def process_code(self, language: str, code: str, 
                     input_data: str = "", env_vars: Dict[str, Any] = None) -> str:
        """使用指定语言的插件处理代码"""
        context = TransformationContext(
            language=language,
            input_data=input_data,
            env_vars=env_vars or {}
        )
        return self.registry.process_code(language, code, context)
    
    def get_plugin_info(self, language: str = None) -> Dict[str, Any]:
        """获取插件信息"""
        if language:
            plugin = self.registry.get_plugin(language)
            if plugin:
                return {
                    "language": language,
                    "extensions": plugin.get_supported_extensions(),
                    "default_filename": plugin.get_default_filename(),
                    "transformers": plugin.get_transformers_info()
                }
            return {}
        else:
            return self.registry.get_all_plugins_info()
    
    def register_custom_plugin(self, plugin):
        """注册自定义插件"""
        self.registry.register_plugin(plugin)
    
    def unregister_plugin(self, language: str):
        """注销插件"""
        self.registry.unregister_plugin(language)
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return self.registry.get_supported_languages()


# 全局扩展管理器实例
extension_manager = ExtensionManager()