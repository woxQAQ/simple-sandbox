from typing import Dict, List

from src.models import ExecutionResult
from src.runtime.base import LanguageRuntime
from src.runtime.extensions.node import nodejs_ast_manager


# 延迟导入以避免循环导入
def get_process_manager():
    from src.utils.process_manager import ProcessManager

    return ProcessManager


class NodeJSRuntime(LanguageRuntime):
    """Node.js运行时实现"""

    def __init__(self, process_manager=None):
        super().__init__("nodejs")

        # 使用提供的进程管理器或创建新的
        if process_manager is None:
            ProcessManager = get_process_manager()
            process_manager = ProcessManager()
        self.process_manager = process_manager

    def get_supported_extensions(self) -> List[str]:
        return [".js", ".mjs", ".cjs"]

    def get_default_filename(self) -> str:
        return "main.js"

    def preprocess_code(self, code: str) -> str:
        """预处理Node.js代码，使用插件系统处理所有增强功能"""
        processed_code = code

        # 使用AST插件系统转换代码
        try:
            context = {"language": "nodejs", "security_warnings": True}
            processed_code = nodejs_ast_manager.transform_code(
                processed_code, context
            )
        except Exception as e:
            # 如果AST转换失败，继续使用原始代码
            print(f"AST转换失败，使用原始代码: {e}")

        return processed_code

    def get_command(self, filename: str = None) -> List[str]:
        """获取Node.js执行命令"""
        # 简化的启动参数
        return ["node"]

    def execute(
        self,
        code: str,
        input_data: str = "",
        env_vars: Dict[str, str] = None,
    ) -> ExecutionResult:
        """执行Node.js代码"""

        # 预处理代码
        processed_code = self.preprocess_code(code)

        # 设置环境变量
        if env_vars is None:
            env_vars = {}

        # 添加输入数据到环境变量
        if input_data:
            env_vars["NODE_INPUT"] = input_data

        # 使用进程管理器执行代码
        return self.process_manager.execute(
            command=self.get_command(),
            code=processed_code,
            input_data=input_data,
            env_vars=env_vars,
            language="nodejs",
        )
