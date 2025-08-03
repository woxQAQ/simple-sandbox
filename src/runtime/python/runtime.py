import subprocess  # nosec B404
import time
import uuid
from typing import Dict

from src.config import runtime_config
from src.models import ExecutionResult, ExecutionStatus
from src.runtime.common.base import LanguageRuntime
from src.runtime.logging_config import create_runtime_logger
from src.runtime.python.extensions import PythonASTContext, python_ast_registry
from src.utils.crypto_utils import CryptoUtils

logger = create_runtime_logger(__name__)


class PythonRuntime(LanguageRuntime):
    """Python运行时实现"""

    def __init__(self):
        super().__init__("python")

    def preprocess_code(
        self, code: str, input_data: str = "", env_vars: Dict[str, str] = {}
    ) -> str:
        """使用扩展系统预处理Python代码"""
        logger.debug(f"开始预处理Python代码 - 代码长度: {len(code)}")

        # 创建AST上下文
        context = PythonASTContext(source_code=code)

        # 使用插件系统转换代码
        try:
            transformed_code = python_ast_registry.transform_code(code, context)

            final_code = transformed_code
            logger.debug(f"代码预处理完成 - 转换后长度: {len(final_code)}")
            return final_code
        except Exception as e:
            logger.error(f"代码预处理失败 - 错误: {e}")
            raise

    def _render_entrypoint(self, enc_code: str) -> str:
        content = ""
        with open("./src/runtime/python/entrypoint.py", "r") as f:
            content = f.read()
            return content.replace("{{code}}", enc_code)

    def execute(
        self,
        code: str,
        input_data: str = "",
        env_vars: dict[str, str] = {},
    ) -> ExecutionResult:
        """执行Python代码"""
        start_time = time.time()

        # 预处理代码
        processed_code = self.preprocess_code(code, input_data, env_vars)

        # 使用固定的Python沙盒目录
        python_sandbox_dir = "/var/sandbox/python"

        encrypted_code, encryption_key = CryptoUtils.encrypt_code(
            processed_code
        )
        entrypoint_content = self._render_entrypoint(
            encrypted_code.decode(),
        )

        import os
        tmp_dir = f"{python_sandbox_dir}/tmp"
        os.makedirs(tmp_dir, exist_ok=True)
        entrypoint_path = f"{tmp_dir}/{uuid.uuid4()}.py"

        with open(entrypoint_path, "w") as f:
            f.write(entrypoint_content)
        # 构建执行命令
        command = [
            runtime_config.get_python_command(),
            entrypoint_path,
            encryption_key,
            str(runtime_config.sandbox_uid),
            str(runtime_config.sandbox_gid),
        ]
        process = subprocess.Popen(  # nosec B603
            command,
            stdin=subprocess.PIPE if input_data else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=python_sandbox_dir,
        )

        stdout, stderr = process.communicate(
            input=input_data if input_data else None,
            timeout=runtime_config.code_execution_timeout,
        )

        execution_time = time.time() - start_time

        # 创建执行结果
        result = ExecutionResult(
            status=(
                ExecutionStatus.SUCCESS
                if process.returncode == 0
                else ExecutionStatus.ERROR
            ),
            stdout=stdout or "",
            stderr=stderr or "",
            execution_time=execution_time,
        )

        return result
