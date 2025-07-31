import subprocess
import time
from typing import Dict, List

from src.config import config
from src.runtime.base import LanguageRuntime
from src.runtime.extensions.python import PythonASTContext, python_ast_registry
from src.runtime.models import ExecutionResult, ExecutionStatus
from src.utils import (
    create_file_in_dir,
    entrypoint_templates,
    set_executable_permission,
    temporary_sandbox_dir,
)
from src.utils.crypto_utils import CryptoUtils


class PythonRuntime(LanguageRuntime):
    """Python运行时实现"""

    def __init__(self):
        super().__init__("python")

    def get_supported_extensions(self) -> List[str]:
        return [".py", ".pyw"]

    def get_default_filename(self) -> str:
        return "main.py"

    def preprocess_code(
        self, code: str, input_data: str = "", env_vars: Dict[str, str] = None
    ) -> str:
        """使用扩展系统预处理Python代码"""
        # 创建AST上下文
        context = PythonASTContext(source_code=code)

        # 使用插件系统转换代码
        transformed_code = python_ast_registry.transform_code(code, context)
        return transformed_code

    def get_command(self, filename: str = None) -> List[str]:
        """获取Python执行命令"""
        return [config.PYTHON_PATH]

    def execute(
        self,
        code: str,
        input_data: str = "",
        env_vars: Dict[str, str] = None,
    ) -> ExecutionResult:
        """执行Python代码"""
        start_time = time.time()

        # 预处理代码
        processed_code = self.preprocess_code(code, input_data, env_vars)

        # 使用上下文管理器创建临时沙盒目录
        with temporary_sandbox_dir() as sandbox_dir:
            # 创建加密工具实例
            crypto_utils = CryptoUtils()

            # 生成加密密钥并加密代码
            encryption_key = crypto_utils.generate_encryption_key()
            encrypted_code = crypto_utils.encrypt_code(
                processed_code, encryption_key
            )

            # 创建entrypoint文件（直接嵌入加密代码）
            entrypoint_path = create_file_in_dir(
                sandbox_dir,
                "entrypoint.py",
                entrypoint_templates.create_entrypoint(
                    "python", encrypted_code, encryption_key
                ),
            )

            # 设置执行权限
            set_executable_permission(entrypoint_path)

            # 构建执行命令（只传递加密密钥）
            command = [
                config.PYTHON_PATH,
                entrypoint_path,
                encryption_key,
            ]

            # 不传递环境变量，保持原有的空环境
            process_env = {}

            try:
                # 执行进程
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE if input_data else None,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=process_env,
                    text=True,
                    cwd=sandbox_dir,
                )

                stdout, stderr = process.communicate(
                    input=input_data if input_data else None,
                    timeout=config.CODE_EXECUTION_TIMEOUT,
                )

                execution_time = time.time() - start_time

                return ExecutionResult(
                    status=(
                        ExecutionStatus.SUCCESS
                        if process.returncode == 0
                        else ExecutionStatus.ERROR
                    ),
                    stdout=stdout or "",
                    stderr=stderr or "",
                    execution_time=execution_time,
                    exit_code=process.returncode,
                    error_message=stderr if process.returncode != 0 else None,
                )

            except subprocess.TimeoutExpired:
                execution_time = time.time() - start_time
                return ExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    stdout="",
                    stderr="Execution timed out",
                    execution_time=execution_time,
                    exit_code=-1,
                    error_message="Execution timed out",
                )

            except Exception as e:
                execution_time = time.time() - start_time
                return ExecutionResult(
                    status=ExecutionStatus.ERROR,
                    stdout="",
                    stderr=str(e),
                    execution_time=execution_time,
                    exit_code=-1,
                    error_message=str(e),
                )
