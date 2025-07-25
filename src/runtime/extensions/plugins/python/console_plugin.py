"""
Python控制台增强插件
独立的功能模块，只包含扩展逻辑
"""

import ast

from ..python_ast_plugin import PythonASTContext, PythonASTPlugin


class PythonConsoleASTPlugin(PythonASTPlugin):
    """Python控制台增强AST插件"""

    def __init__(self):
        super().__init__("python_console_ast", priority=90)

    def should_transform(self, node: ast.AST, context: PythonASTContext) -> bool:
        """检测print调用"""
        return (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "print"
        )

    def transform(self, node: ast.AST, context: PythonASTContext) -> ast.AST:
        """增强print调用"""
        if not isinstance(node, ast.Expr):
            return node

        # 创建增强的print调用
        timestamp_call = ast.Call(
            func=ast.Attribute(
                value=ast.Name(id="datetime", ctx=ast.Load()),
                attr="now",
                ctx=ast.Load(),
            ),
            args=[],
            keywords=[],
        )

        format_call = ast.Call(
            func=ast.Attribute(value=timestamp_call, attr="isoformat", ctx=ast.Load()),
            args=[],
            keywords=[],
        )

        # 创建f-string: f"[{timestamp}] {args...}"
        format_str = ast.JoinedStr(
            values=[
                ast.Constant(value="["),
                ast.FormattedValue(value=format_call, conversion=-1),
                ast.Constant(value="] "),
            ]
            + [ast.FormattedValue(value=arg, conversion=-1) for arg in node.value.args]
        )

        # 替换为新的print调用
        new_print = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="print", ctx=ast.Load()),
                args=[format_str] + node.value.args,
                keywords=node.value.keywords,
            )
        )

        return new_print