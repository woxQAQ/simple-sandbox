"""
Python控制台增强插件
独立的功能模块，只包含扩展逻辑
"""

import ast

from src.runtime.python.transformer import PythonASTPlugin


class PythonConsoleASTPlugin(PythonASTPlugin):
    """Python控制台增强AST插件"""

    def __init__(self):
        super().__init__("python_console_ast", priority=90)
        self.datetime_imported = False

    def should_transform(self, node: ast.AST) -> bool:
        """检测print调用"""
        return (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "print"
        )

    def transform(self, node: ast.AST) -> ast.AST:
        """增强print调用"""
        if not isinstance(node, ast.Expr):
            return node

        # 检查是否为print调用
        if not (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "print"
        ):
            return node

        # 创建简单的前缀字符串
        prefix = ast.Constant(value="[CONSOLE] ")

        # 如果有参数，创建简单的前缀而不是f-string，以避免语法错误
        if node.value.args:
            prefix_str = ast.Constant(value="[CONSOLE] ")

            # 替换为新的print调用：print("[CONSOLE] ", ...args)
            new_print = ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="print", ctx=ast.Load()),
                    args=[prefix_str] + node.value.args,
                    keywords=node.value.keywords,
                )
            )
        else:
            # 无参数的print调用
            new_print = ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="print", ctx=ast.Load()),
                    args=[prefix],
                    keywords=node.value.keywords,
                )
            )

        return new_print
