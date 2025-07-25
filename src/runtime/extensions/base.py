from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class TransformationContext:
    """代码转换上下文"""

    language: str
    input_data: str = ""
    env_vars: Dict[str, str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}
        if self.metadata is None:
            self.metadata = {}


class CodeTransformer(ABC):
    """代码转换器抽象基类"""

    def __init__(self, name: str, priority: int = 100):
        self.name = name
        self.priority = priority

    @abstractmethod
    def detect(self, code: str, context: TransformationContext) -> bool:
        """检测代码是否需要转换"""
        pass

    @abstractmethod
    def transform(self, code: str, context: TransformationContext) -> str:
        """执行代码转换"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """获取转换器信息"""
        return {
            "name": self.name,
            "priority": self.priority,
            "type": self.__class__.__name__,
        }


class LanguagePlugin(ABC):
    """语言插件抽象基类"""

    def __init__(self, language: str):
        self.language = language
        self.transformers: Dict[str, CodeTransformer] = {}

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        pass

    @abstractmethod
    def get_default_filename(self) -> str:
        """获取默认文件名"""
        pass

    def register_transformer(self, transformer: CodeTransformer):
        """注册代码转换器"""
        self.transformers[transformer.name] = transformer

    def unregister_transformer(self, name: str):
        """注销代码转换器"""
        if name in self.transformers:
            del self.transformers[name]

    def process_code(self, code: str, context: TransformationContext) -> str:
        """使用所有注册的转换器处理代码"""
        processed_code = code

        # 按优先级排序转换器
        sorted_transformers = sorted(
            self.transformers.values(), key=lambda t: t.priority, reverse=True
        )

        for transformer in sorted_transformers:
            try:
                if transformer.detect(processed_code, context):
                    processed_code = transformer.transform(processed_code, context)
            except Exception as e:
                # 记录错误但不中断处理
                print(f"Transformer {transformer.name} failed: {e}")

        return processed_code

    def get_transformers_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有转换器信息"""
        return {
            name: transformer.get_info()
            for name, transformer in self.transformers.items()
        }


class PluginRegistry:
    """插件注册表 - 管理所有语言插件"""

    def __init__(self):
        self.plugins: Dict[str, LanguagePlugin] = {}

    def register_plugin(self, plugin: LanguagePlugin):
        """注册语言插件"""
        self.plugins[plugin.language] = plugin

    def unregister_plugin(self, language: str):
        """注销语言插件"""
        if language in self.plugins:
            del self.plugins[language]

    def get_plugin(self, language: str) -> Optional[LanguagePlugin]:
        """获取指定语言的插件"""
        return self.plugins.get(language)

    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        return list(self.plugins.keys())

    def process_code(
        self, language: str, code: str, context: TransformationContext
    ) -> str:
        """使用指定语言的插件处理代码"""
        plugin = self.get_plugin(language)
        if plugin:
            return plugin.process_code(code, context)
        return code

    def get_all_plugins_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有插件的信息"""
        return {
            language: {
                "language": language,
                "extensions": plugin.get_supported_extensions(),
                "default_filename": plugin.get_default_filename(),
                "transformers": plugin.get_transformers_info(),
            }
            for language, plugin in self.plugins.items()
        }


# 全局插件注册表
plugin_registry = PluginRegistry()
