import os
import subprocess  # nosec B404
import time

from src.config import runtime_config
from src.models import ExecutionResult, ExecutionStatus
from src.runtime.common.base import LanguageRuntime
from src.runtime.logging_config import create_runtime_logger
from src.runtime.nodejs.utils import NodeJSRuntimeUtils
from src.utils.crypto_utils import CryptoUtils

logger = create_runtime_logger(__name__)


class NodeJSRuntime(LanguageRuntime):
    """Node.js运行时实现"""

    def __init__(self):
        super().__init__("nodejs")

    def preprocess_code(self, code: str) -> str:
        """预处理Node.js代码（已移除transformer功能）"""
        logger.debug(f"开始预处理Node.js代码 - 代码长度: {len(code)}")

        # 直接返回原始代码，不再使用AST转换
        processed_code = code

        logger.debug(f"Node.js代码预处理完成 - 长度: {len(processed_code)}")

        return processed_code

    def _render_entrypoint(self, enc_code: str) -> str:
        content = ""
        with open("./src/runtime/nodejs/entrypoint.js", "r") as f:
            content = f.read()
            return content.replace("{{ code }}", enc_code)

    def execute(
        self,
        code: str,
        input_data: str = "",
        env_vars: dict[str, str] = {},
    ) -> ExecutionResult:
        """执行Node.js代码"""
        start_time = time.time()

        # 预处理代码
        processed_code = self.preprocess_code(code)

        # 使用新的Node.js沙盒目录管理器
        with NodeJSRuntimeUtils.nodejs_sandbox_dir() as sandbox_dir:
            # 使用公共工具加密代码
            encrypted_code, encryption_key = CryptoUtils.encrypt_code(
                processed_code
            )

            _code = self._render_entrypoint(encrypted_code)

            entrypoint_path = f"{sandbox_dir}/runtime/entrypoint.js"
            # 创建entrypoint文件
            with open(entrypoint_path, "w") as f:
                f.write(_code)

            # 构建执行命令
            command = [
                runtime_config.get_nodejs_command(),
                entrypoint_path,
                encryption_key,
                str(runtime_config.sandbox_uid),
                str(runtime_config.sandbox_gid),
            ]

            # 执行进程，在preexecfn中设置seccomp安全限制
            process = subprocess.Popen(  # nosec B603
                command,
                stdin=subprocess.PIPE if input_data else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=sandbox_dir,
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
