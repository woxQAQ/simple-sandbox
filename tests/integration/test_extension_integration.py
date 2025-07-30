"""
扩展集成测试
测试扩展系统的集成功能
"""

import ast
from unittest.mock import Mock, patch

from src.runtime.extensions.node import NodeJSASTManager
from src.runtime.extensions.python import PythonASTRegistry
from src.runtime.transformer.python import PythonASTContext


class MockPythonASTPlugin:
    """模拟Python AST插件用于集成测试"""

    def __init__(
        self, name="mock_plugin", priority=100, should_transform_result=True
    ):
        self.name = name
        self.priority = priority
        self.should_transform_result = should_transform_result
        self.transform_called = False
        self.should_transform_called = False

    def should_transform(self, node: ast.AST) -> bool:
        """模拟should_transform方法"""
        self.should_transform_called = True
        return self.should_transform_result

    def transform(self, node: ast.AST) -> ast.AST:
        """模拟transform方法"""
        self.transform_called = True
        return node

    def visit(self, tree: ast.AST) -> ast.AST:
        """模拟visit方法"""
        if self.should_transform(tree):
            return self.transform(tree)
        return tree


class TestExtensionIntegration:
    """扩展集成测试"""

    def test_python_extension_integration(self):
        """测试Python扩展集成"""
        from src.runtime.extensions.python import python_ast_registry

        # 测试全局注册表存在
        assert python_ast_registry is not None

    def test_nodejs_extension_integration(self):
        """测试Node.js扩展集成"""
        from src.runtime.extensions.node import (
            nodejs_ast_manager,
            nodejs_ast_registry,
        )

        # 测试全局管理器和注册表存在
        assert nodejs_ast_manager is not None
        assert nodejs_ast_registry is not None

    def test_extension_error_handling(self):
        """测试扩展错误处理"""
        plugin = MockPythonASTPlugin(
            "test_plugin", should_transform_result=False
        )

        tree = ast.parse("print('hello')")

        result = plugin.visit(tree)

        # 插件不应该转换但也不应该出错
        assert result is not None
        assert plugin.should_transform_called
        assert not plugin.transform_called

    def test_extension_metadata_handling(self):
        """测试扩展元数据处理"""
        plugin = MockPythonASTPlugin("test_plugin")
        tree = ast.parse("print('hello')")

        result = plugin.visit(tree)

        assert result is not None
        assert plugin.should_transform_called

    def test_extension_plugin_registration(self):
        """测试插件注册"""
        registry = PythonASTRegistry()
        plugin = MockPythonASTPlugin("test_plugin")

        registry.register(plugin)

        assert len(registry.plugins) == 1
        assert registry.plugins[0] == plugin

    def test_extension_multiple_plugins(self):
        """测试多个插件"""
        registry = PythonASTRegistry()
        plugin1 = MockPythonASTPlugin("plugin1", priority=50)
        plugin2 = MockPythonASTPlugin("plugin2", priority=100)

        registry.register(plugin1)
        registry.register(plugin2)

        assert len(registry.plugins) == 2
        # 插件应该按优先级排序
        assert registry.plugins[0].priority == 100
        assert registry.plugins[1].priority == 50

    def test_extension_code_transformation(self):
        """测试代码转换"""
        registry = PythonASTRegistry()
        plugin = MockPythonASTPlugin("test_plugin")
        registry.register(plugin)

        context = PythonASTContext(source_code="print('hello')")

        with patch(
            "src.runtime.transformer.python.PythonASTTransformer.transform"
        ) as mock_transform:
            mock_transform.return_value = "transformed_code"

            result = registry.transform_code("print('hello')", context)

            assert result == "transformed_code"
            mock_transform.assert_called_once()

    def test_extension_no_plugins_transformation(self):
        """测试无插件时的代码转换"""
        registry = PythonASTRegistry()
        context = PythonASTContext(source_code="print('hello')")

        result = registry.transform_code("print('hello')", context)

        assert result == "print('hello')"

    def test_extension_nodejs_manager_integration(self):
        """测试Node.js管理器集成"""
        with patch("os.path.join") as mock_join:
            mock_join.return_value = "/fake/path/transformer.js"

            manager = NodeJSASTManager()
            assert manager.js_transformer_path == "/fake/path/transformer.js"

    def test_extension_nodejs_transformation(self):
        """测试Node.js转换"""
        with patch("os.path.join") as mock_join:
            mock_join.return_value = "/fake/path/transformer.js"

            with patch("subprocess.run") as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = (
                    '{"success": true, "transformed": "transformed_code"}'
                )
                mock_run.return_value = mock_result

                manager = NodeJSASTManager()
                result = manager.transform_code(
                    "original_code", {"key": "value"}
                )

                assert result == "transformed_code"

    def test_extension_cross_language_compatibility(self):
        """测试跨语言兼容性"""
        # 测试Python和Node.js扩展系统可以共存
        from src.runtime.extensions.node import nodejs_ast_manager
        from src.runtime.extensions.python import python_ast_registry

        assert python_ast_registry is not None
        assert nodejs_ast_manager is not None

        # 它们应该可以独立工作
        assert hasattr(python_ast_registry, "plugins")
        assert hasattr(nodejs_ast_manager, "js_transformer_path")

    def test_extension_error_recovery(self):
        """测试错误恢复"""
        # 测试Python扩展错误恢复
        registry = PythonASTRegistry()
        context = PythonASTContext(source_code="print('hello')")

        # 语法错误应该返回原代码
        result = registry.transform_code("invalid syntax", context)
        assert result == "invalid syntax"

    def test_extension_context_handling(self):
        """测试上下文处理"""
        registry = PythonASTRegistry()

        # 测试不同的上下文
        context1 = PythonASTContext(source_code="print('hello')")
        context2 = PythonASTContext(source_code="print('world')")

        result1 = registry.transform_code("print('hello')", context1)
        result2 = registry.transform_code("print('world')", context2)

        assert result1 == "print('hello')"
        assert result2 == "print('world')"

    def test_extension_performance_considerations(self):
        """测试性能考虑"""
        # 测试插件优先级排序
        registry = PythonASTRegistry()

        # 添加多个不同优先级的插件
        for i in range(10):
            plugin = MockPythonASTPlugin(f"plugin_{i}", priority=i * 10)
            registry.register(plugin)

        # 验证插件按优先级排序
        priorities = [p.priority for p in registry.plugins]
        assert priorities == sorted(priorities, reverse=True)

    def test_extension_extensibility(self):
        """测试可扩展性"""
        # 测试可以动态添加插件
        registry = PythonASTRegistry()

        # 初始状态
        assert len(registry.plugins) == 0

        # 动态添加插件
        plugin1 = MockPythonASTPlugin("dynamic_plugin_1")
        plugin2 = MockPythonASTPlugin("dynamic_plugin_2")

        registry.register(plugin1)
        registry.register(plugin2)

        assert len(registry.plugins) == 2
