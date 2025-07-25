"""
Node.js原生AST插件系统
使用JavaScript的AST解析器（运行时注入）
分离AST解析和插件扩展逻辑
"""

import json
import subprocess
import os
from typing import Dict, List, Any, Optional


class NodeJSASTPlugin:
    """Node.js AST插件基类"""

    def __init__(self, name: str, priority: int = 100):
        self.name = name
        self.priority = priority

    def should_transform(
        self, ast_data: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """判断是否应该应用此插件"""
        raise NotImplementedError("子类必须实现should_transform方法")

    def transform(self, ast_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """转换AST并返回代码"""
        raise NotImplementedError("子类必须实现transform方法")


class NodeJSASTRegistry:
    """Node.js AST插件注册表"""

    def __init__(self):
        self.plugins: List[NodeJSASTPlugin] = []

    def register(self, plugin: NodeJSASTPlugin):
        """注册插件"""
        self.plugins.append(plugin)
        self.plugins.sort(key=lambda p: p.priority, reverse=True)


class NodeJSASTManager:
    """Node.js AST管理器 - 通过Node进程调用acorn"""

    def __init__(self):
        self.js_transformer_path = os.path.join(
            os.path.dirname(__file__), "js_ast_transformer.js"
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


# 注册表
nodejs_ast_registry = NodeJSASTRegistry()
