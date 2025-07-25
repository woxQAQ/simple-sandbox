"""
Node.js原生AST插件系统
使用JavaScript的AST解析器（运行时注入）
分离AST解析和插件扩展逻辑
"""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Dict

@dataclass
class NodeASTPlugin:
    name: str
    priority: int

def get_plugins() :
    """获取所有插件"""
    path = Path.cwd() / "plugins/nodejs"
    plugins = []
    for file in path.glob("*.js"):
        if file.name != "index.js":
            plugin = NodeASTPlugin(name=file.stem, priority=100)
            plugins.append(plugin)
    return plugins


class NodeASTRegistry:
    """Python AST插件注册表"""

    def __init__(self):
        self.plugins = get_plugins()

    def register(self, plugin: NodeASTPlugin):
        """注册插件"""
        self.plugins.append(plugin)
        # 按优先级排序
        self.plugins.sort(key=lambda p: p.priority, reverse=True)



class NodeJSASTManager:
    """Node.js AST管理器 - 通过Node进程调用acorn"""

    def __init__(self):
        self.js_transformer_path = os.path.join(
            os.path.dirname(__file__), "transformer/nodejs/transformer.js"
        )

    def transform_code(self, code: str, context: Dict[str, Any] = None) -> str:
        """通过Node.js进程转换JavaScript代码"""
        if context is None:
            context = {}

        try:
            # 调用Node.js转换器
            result = subprocess.run(
                ["node", self.js_transformer_path],
                input=json.dumps({"code": code, "context": context}),
                text=True,
                capture_output=True,
                timeout=10,
            )

            if result.returncode == 0:
                output = json.loads(result.stdout)
                if output.get("success"):
                    return output.get("transformed", code)
                else:
                    return code
            else:
                print(f"Node.js转换错误: {result.stderr}")
                return code

        except subprocess.TimeoutExpired:
            print("Node.js转换超时")
            return code
        except FileNotFoundError:
            print("Node.js未找到，跳过JavaScript AST转换")
            return code
        except Exception as e:
            print(f"AST转换失败: {e}")
            return code


# 全局管理器
nodejs_ast_manager = NodeJSASTManager()
nodejs_ast_registry = NodeASTRegistry()
