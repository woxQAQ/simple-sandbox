import subprocess
import sys
import time
from typing import Dict, List

from src.config import config
from src.runtime.common.base import LanguageRuntime
from src.runtime.common.models import ExecutionResult, ExecutionStatus
from src.runtime.nodejs.extensions import nodejs_ast_manager
from src.security import create_secure_process
from src.utils import (
    create_file_in_dir,
    entrypoint_templates,
    set_executable_permission,
    temporary_sandbox_dir,
)
from src.utils.crypto_utils import CryptoUtils


class NodeJSRuntime(LanguageRuntime):
    """Node.js运行时实现"""

    def __init__(self):
        super().__init__("nodejs")

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
        return [config.NODEJS_PATH]

    def _setup_seccomp_security(self):
        """在子进程中设置seccomp安全限制"""
        try:
            # 使用安全管理器设置seccomp过滤器
            create_secure_process(
                language="nodejs",
                uid=1000,
                gid=1000,
                library_dir="/var/sandbox/nodejs",
            )
        except Exception as e:
            # 如果seccomp设置失败，记录错误但继续执行
            print(f"seccomp安全设置失败: {e}", file=sys.stderr)

    def execute(
        self,
        code: str,
        input_data: str = "",
        env_vars: Dict[str, str] | None = None,
    ) -> ExecutionResult:
        """执行Node.js代码"""
        start_time = time.time()

        # 预处理代码
        processed_code = self.preprocess_code(code)

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
                "entrypoint.js",
                entrypoint_templates.create_entrypoint(
                    "nodejs", encrypted_code, encryption_key, "1000", "1000"
                ),
            )

            # 设置执行权限
            set_executable_permission(entrypoint_path)

            # 构建执行命令（只传递加密密钥）
            node_command = self.get_command()
            command = node_command + [entrypoint_path, encryption_key]

            # 不传递环境变量，保持原有的空环境
            process_env = {}

            try:
                # 执行进程，在preexecfn中设置seccomp安全限制
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE if input_data else None,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=process_env,
                    text=True,
                    cwd=sandbox_dir,
                    preexec_fn=self._setup_seccomp_security,
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
