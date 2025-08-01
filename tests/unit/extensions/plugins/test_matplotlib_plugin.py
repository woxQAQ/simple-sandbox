"""
Matplotlib插件测试
测试Matplotlib AST插件功能
"""

import ast

from src.runtime.common.plugins.python import MatplotlibASTPlugin


class TestMatplotlibASTPlugin:
    """Matplotlib插件测试"""

    def setup_method(self):
        """测试前设置"""
        self.plugin = MatplotlibASTPlugin()

    def test_plugin_creation(self):
        """测试插件创建"""
        assert self.plugin.name == "matplotlib_ast"
        assert self.plugin.priority == 95

    def test_should_transform_matplotlib_import(self):
        """测试检测matplotlib导入"""

        # 创建matplotlib导入的AST节点
        tree = ast.parse("import matplotlib")
        import_node = tree.body[0]

        result = self.plugin.should_transform(import_node)
        assert result is True

    def test_should_transform_matplotlib_from_import(self):
        """测试检测matplotlib from导入"""

        # 创建matplotlib from导入的AST节点
        tree = ast.parse("from matplotlib import pyplot")
        import_node = tree.body[0]

        result = self.plugin.should_transform(import_node)
        assert result is True

    def test_should_transform_matplotlib_multiple_import(self):
        """测试检测matplotlib多模块导入"""

        # 创建matplotlib多模块导入的AST节点
        tree = ast.parse("from matplotlib import pyplot, pylab")
        import_node = tree.body[0]

        result = self.plugin.should_transform(import_node)
        assert result is True

    def test_should_transform_matplotlib_alias_import(self):
        """测试检测matplotlib别名导入"""

        # 创建matplotlib别名导入的AST节点
        tree = ast.parse("import matplotlib as plt")
        import_node = tree.body[0]

        result = self.plugin.should_transform(import_node)
        assert result is True

    def test_should_transform_matplotlib_from_alias_import(self):
        """测试检测matplotlib from别名导入"""

        # 创建matplotlib from别名导入的AST节点
        tree = ast.parse("from matplotlib import pyplot as plt")
        import_node = tree.body[0]

        result = self.plugin.should_transform(import_node)
        assert result is True

    def test_should_transform_non_matplotlib_import(self):
        """测试非matplotlib导入"""

        # 创建非matplotlib导入的AST节点
        tree = ast.parse("import os")
        import_node = tree.body[0]

        result = self.plugin.should_transform(import_node)
        assert result is False

    def test_should_transform_other_library_import(self):
        """测试其他库导入"""

        # 创建其他库导入的AST节点
        tree = ast.parse("import numpy")
        import_node = tree.body[0]

        result = self.plugin.should_transform(import_node)
        assert result is False

    def test_should_transform_wrong_node_type(self):
        """测试错误节点类型"""

        # 创建print调用的AST节点
        tree = ast.parse("print('hello')")
        print_node = tree.body[0]

        result = self.plugin.should_transform(print_node)
        assert result is False

    def test_should_transform_function_call(self):
        """测试函数调用"""

        # 创建函数调用的AST节点
        tree = ast.parse("my_function()")
        call_node = tree.body[0]

        result = self.plugin.should_transform(call_node)
        assert result is False

    def test_transform_matplotlib_import(self):
        """测试转换matplotlib导入"""

        # 创建matplotlib导入的AST节点
        tree = ast.parse("import matplotlib")
        import_node = tree.body[0]

        result = self.plugin.transform(import_node)

        # 对于导入节点，应该返回原节点（因为transform方法只处理Module节点）
        assert result == import_node

    def test_transform_matplotlib_from_import(self):
        """测试转换matplotlib from导入"""

        # 创建matplotlib from导入的AST节点
        tree = ast.parse("from matplotlib import pyplot")
        import_node = tree.body[0]

        result = self.plugin.transform(import_node)

        # 对于导入节点，应该返回原节点
        assert result == import_node

    def test_transform_module_node(self):
        """测试转换Module节点"""

        # 创建Module节点
        tree = ast.parse("import matplotlib\nprint('hello')")
        module_node = tree

        result = self.plugin.transform(module_node)

        # Module节点应该被处理
        assert result is not None

    def test_transform_wrong_node_type(self):
        """测试转换错误节点类型"""

        # 创建print调用的AST节点
        tree = ast.parse("print('hello')")
        print_node = tree.body[0]

        result = self.plugin.transform(print_node)

        # 错误节点类型应该返回原节点
        assert result == print_node

    def test_plugin_visit_method(self):
        """测试插件visit方法"""

        # 创建matplotlib导入的AST节点
        tree = ast.parse("import matplotlib")
        import_node = tree.body[0]

        result = self.plugin.visit(import_node)

        # 应该返回原节点（因为transform方法只处理Module节点）
        assert result == import_node

    def test_plugin_visit_non_import(self):
        """测试插件visit非导入节点"""

        # 创建print调用的AST节点
        tree = ast.parse("print('hello')")
        print_node = tree.body[0]

        result = self.plugin.visit(print_node)

        # 非导入节点应该返回原节点
        assert result == print_node
