"""
Python控制台插件测试
测试Python控制台AST插件功能
"""

import ast

from src.runtime.common.plugins.python import PythonConsoleASTPlugin


class TestPythonConsoleASTPlugin:
    """Python控制台插件测试"""

    def setup_method(self):
        """测试前设置"""
        self.plugin = PythonConsoleASTPlugin()

    def test_plugin_creation(self):
        """测试插件创建"""
        assert self.plugin.name == "python_console_ast"
        assert self.plugin.priority == 90

    def test_should_transform_print_call(self):
        """测试检测print调用"""

        # 创建print调用的AST节点
        tree = ast.parse("print('hello')")
        print_node = tree.body[0]

        result = self.plugin.should_transform(print_node)
        assert result is True

    def test_should_transform_print_call_with_args(self):
        """测试检测带参数的print调用"""

        # 创建print调用的AST节点
        tree = ast.parse("print('hello', 'world')")
        print_node = tree.body[0]

        result = self.plugin.should_transform(print_node)
        assert result is True

    def test_should_transform_print_call_with_kwargs(self):
        """测试检测带关键字参数的print调用"""

        # 创建print调用的AST节点
        tree = ast.parse("print('hello', end='')")
        print_node = tree.body[0]

        result = self.plugin.should_transform(print_node)
        assert result is True

    def test_should_transform_non_print_call(self):
        """测试非print调用"""

        # 创建非print调用的AST节点
        tree = ast.parse("len('hello')")
        len_node = tree.body[0]

        result = self.plugin.should_transform(len_node)
        assert result is False

    def test_should_transform_other_function_call(self):
        """测试其他函数调用"""

        # 创建其他函数调用的AST节点
        tree = ast.parse("my_function()")
        call_node = tree.body[0]

        result = self.plugin.should_transform(call_node)
        assert result is False

    def test_should_transform_wrong_node_type(self):
        """测试错误节点类型"""

        # 创建赋值语句的AST节点
        tree = ast.parse("x = 1")
        assign_node = tree.body[0]

        result = self.plugin.should_transform(assign_node)
        assert result is False

    def test_should_transform_import_node(self):
        """测试导入节点"""

        # 创建导入的AST节点
        tree = ast.parse("import os")
        import_node = tree.body[0]

        result = self.plugin.should_transform(import_node)
        assert result is False

    def test_should_transform_expression_node(self):
        """测试表达式节点"""

        # 创建表达式的AST节点
        tree = ast.parse("1 + 2")
        expr_node = tree.body[0]

        result = self.plugin.should_transform(expr_node)
        assert result is False

    def test_transform_print_call(self):
        """测试转换print调用"""

        # 创建print调用的AST节点
        tree = ast.parse("print('hello')")
        print_node = tree.body[0]

        result = self.plugin.transform(print_node)

        # 结果应该是一个Expr节点
        assert isinstance(result, ast.Expr)
        # 内部应该是一个Call节点
        assert isinstance(result.value, ast.Call)
        # 函数名应该是print
        assert isinstance(result.value.func, ast.Name)
        assert result.value.func.id == "print"

    def test_transform_print_call_with_args(self):
        """测试转换带参数的print调用"""

        # 创建print调用的AST节点
        tree = ast.parse("print('hello', 'world')")
        print_node = tree.body[0]

        result = self.plugin.transform(print_node)

        # 结果应该是一个Expr节点
        assert isinstance(result, ast.Expr)
        # 内部应该是一个Call节点
        assert isinstance(result.value, ast.Call)
        # 函数名应该是print
        assert isinstance(result.value.func, ast.Name)
        assert result.value.func.id == "print"
        # 应该有参数（格式化字符串 + 原始参数）
        assert len(result.value.args) == 3

    def test_transform_non_print_call(self):
        """测试转换非print调用"""

        # 创建非print调用的AST节点
        tree = ast.parse("len('hello')")
        len_node = tree.body[0]

        result = self.plugin.transform(len_node)

        # 非print调用应该返回原节点
        assert result == len_node

    def test_transform_wrong_node_type(self):
        """测试转换错误节点类型"""

        # 创建赋值语句的AST节点
        tree = ast.parse("x = 1")
        assign_node = tree.body[0]

        result = self.plugin.transform(assign_node)

        # 错误节点类型应该返回原节点
        assert result == assign_node

    def test_plugin_visit_method(self):
        """测试插件visit方法"""

        # 创建print调用的AST节点
        tree = ast.parse("print('hello')")
        print_node = tree.body[0]

        result = self.plugin.visit(print_node)

        # 应该返回转换后的节点
        assert isinstance(result, ast.Expr)
        assert isinstance(result.value, ast.Call)
        assert isinstance(result.value.func, ast.Name)
        assert result.value.func.id == "print"

    def test_plugin_visit_non_print(self):
        """测试插件visit非print节点"""

        # 创建非print调用的AST节点
        tree = ast.parse("len('hello')")
        len_node = tree.body[0]

        result = self.plugin.visit(len_node)

        # 非print节点应该返回原节点
        assert result == len_node
