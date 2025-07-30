"""
Matplotlib增强插件
独立的功能模块，只包含扩展逻辑
"""

import ast

from src.runtime.transformer.python import (
    PythonASTPlugin,
)


class MatplotlibASTPlugin(PythonASTPlugin):
    """Matplotlib AST插件"""

    def __init__(self):
        super().__init__("matplotlib_ast", priority=95)

    def should_transform(self, node: ast.AST) -> bool:
        """检测matplotlib导入"""
        if isinstance(node, ast.Import):
            return any(
                alias.name.startswith("matplotlib")
                or alias.name == "matplotlib.pyplot"
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            return node.module and "matplotlib" in node.module
        return False

    def transform(self, node: ast.AST) -> ast.AST:
        """添加matplotlib配置"""
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            return node

        # 创建matplotlib配置代码
        config_code = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import datetime

# 图形捕获函数
def _capture_plot():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] ![plot](data:image/png;base64,{img_base64})")

# 替换plt.show
if 'plt' in globals():
    plt.show = _capture_plot
"""

        config_nodes = ast.parse(config_code).body

        # 如果是模块，添加配置
        if isinstance(node, ast.Module):
            new_body = config_nodes + node.body
            return ast.Module(body=new_body, type_ignores=[])

        return node
