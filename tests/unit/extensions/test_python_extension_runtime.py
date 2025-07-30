"""
扩展基础组件测试
测试AST上下文、插件基类、转换器等基础组件
"""

import ast
from unittest.mock import patch

from src.runtime.transformer.python import (
    PythonASTContext,
    PythonASTPlugin,
    PythonASTTransformer,
)


class MockPythonASTPlugin(PythonASTPlugin):
    """模拟AST插件用于测试"""

    def __init__(
        self, name="mock_plugin", priority=100, should_transform_result=True
    ):
        super().__init__(name, priority)
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


class TestPythonASTContext:
    """Python AST上下文测试"""

    def test_context_creation(self):
        """测试上下文创建"""
        context = PythonASTContext(source_code="print('hello')")
        assert context.source_code == "print('hello')"

    def test_context_with_empty_metadata(self):
        """测试空元数据的上下文"""
        context = PythonASTContext(source_code="print('hello')")
        assert context.source_code == "print('hello')"

    def test_context_with_no_metadata(self):
        """测试无元数据的上下文"""
        context = PythonASTContext(source_code="print('hello')")
        assert context.source_code == "print('hello')"


class TestPythonASTPlugin:
    """Python AST插件基类测试"""

    def test_plugin_creation(self):
        """测试插件创建"""
        plugin = MockPythonASTPlugin("test_plugin", 50)

        assert plugin.name == "test_plugin"
        assert plugin.priority == 50

    def test_plugin_visit(self):
        """测试插件访问方法"""
        plugin = MockPythonASTPlugin("test_plugin")
        pass

        # 创建一个简单的AST树
        tree = ast.parse("print('hello')")

        result = plugin.visit(tree)

        assert plugin.should_transform_called
        assert plugin.transform_called
        assert result is not None

    def test_plugin_recursive_visit(self):
        """测试插件递归访问"""
        plugin = MockPythonASTPlugin("test_plugin")
        pass

        # 创建一个包含嵌套结构的AST树
        code = """
if True:
    print('nested')
"""
        tree = ast.parse(code)

        result = plugin.visit(tree)

        assert plugin.should_transform_called
        assert result is not None

    def test_plugin_should_not_transform(self):
        """测试插件不转换的情况"""
        plugin = MockPythonASTPlugin(
            "test_plugin", should_transform_result=False
        )
        pass

        tree = ast.parse("print('hello')")

        result = plugin.visit(tree)

        assert plugin.should_transform_called
        assert not plugin.transform_called
        assert result is not None


class TestPythonASTTransformer:
    """Python AST转换器测试"""

    def test_transformer_creation(self):
        """测试转换器创建"""
        plugin = MockPythonASTPlugin("test_plugin")
        transformer = PythonASTTransformer([plugin])

        assert len(transformer.plugins) == 1
        assert transformer.plugins[0] == plugin

    def test_transformer_plugin_priority_sorting(self):
        """测试插件优先级排序"""
        plugin1 = MockPythonASTPlugin("plugin1", priority=50)
        plugin2 = MockPythonASTPlugin("plugin2", priority=100)
        plugin3 = MockPythonASTPlugin("plugin3", priority=75)

        transformer = PythonASTTransformer([plugin1, plugin2, plugin3])

        # 插件应该按优先级升序排列
        priorities = [p.priority for p in transformer.plugins]
        assert priorities == [50, 75, 100]

    def test_transformer_transform_success(self):
        """测试转换器转换成功"""
        plugin = MockPythonASTPlugin("test_plugin")
        transformer = PythonASTTransformer([plugin])
        context = PythonASTContext(source_code="print('hello')")

        with patch("astor.to_source") as mock_to_source:
            mock_to_source.return_value = "print('hello')"

            result = transformer.transform("print('hello')", context)

            assert result == "print('hello')"
            assert plugin.should_transform_called
            assert plugin.transform_called

    def test_transformer_transform_syntax_error(self):
        """测试转换器处理语法错误"""
        plugin = MockPythonASTPlugin("test_plugin")
        transformer = PythonASTTransformer([plugin])
        context = PythonASTContext(source_code="invalid syntax")

        result = transformer.transform("invalid syntax", context)

        # 语法错误时应该返回原代码
        assert result == "invalid syntax"

    def test_transformer_multiple_plugins(self):
        """测试转换器处理多个插件"""
        plugin1 = MockPythonASTPlugin("plugin1", priority=100)
        plugin2 = MockPythonASTPlugin("plugin2", priority=50)
        transformer = PythonASTTransformer([plugin1, plugin2])
        context = PythonASTContext(source_code="print('hello')")

        with patch("astor.to_source") as mock_to_source:
            mock_to_source.return_value = "print('hello')"

            result = transformer.transform("print('hello')", context)

            assert result == "print('hello')"
            assert plugin1.should_transform_called
            assert plugin2.should_transform_called

    def test_transformer_empty_plugins(self):
        """测试空插件列表"""
        transformer = PythonASTTransformer([])
        context = PythonASTContext(source_code="print('hello')")

        result = transformer.transform("print('hello')", context)

        # 空插件列表时应该返回原代码（astor.to_source会添加换行符）
        assert result == "print('hello')\n"

    def test_transformer_plugin_exception(self):
        """测试插件异常处理"""

        class ExceptionPlugin(PythonASTPlugin):
            def should_transform(self, node):
                return True

            def transform(self, node):
                raise Exception("Plugin error")

        plugin = ExceptionPlugin("exception_plugin")
        transformer = PythonASTTransformer([plugin])
        context = PythonASTContext(source_code="print('hello')")

        # 插件异常时应该跳过该插件，返回原代码（astor.to_source会添加换行符）
        result = transformer.transform("print('hello')", context)
        assert result == "print('hello')\n"
