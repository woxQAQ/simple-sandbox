import os
import subprocess  # nosec B404
import sys
import time
import traceback
from typing import Dict, List

from src.config import runtime_config
from src.runtime.common.base import LanguageRuntime
from src.runtime.common.models import ExecutionResult, ExecutionStatus
from src.runtime.logging_config import create_runtime_logger
from src.runtime.nodejs.extensions import nodejs_ast_manager
from src.security import create_secure_process
from src.utils import (
    create_file_in_dir,
    entrypoint_templates,
    set_executable_permission,
    temporary_sandbox_dir,
)
from src.utils.crypto_utils import CryptoUtils

logger = create_runtime_logger(__name__)


class NodeJSRuntime(LanguageRuntime):
    """Node.js运行时实现"""

    def __init__(self):
        super().__init__("nodejs")

    def get_supported_extensions(self) -> List[str]:
        return [".js", ".mjs", ".cjs"]

    def preprocess_code(self, code: str) -> str:
        """预处理Node.js代码，使用插件系统处理所有增强功能"""
        if runtime_config.debug_mode:
            logger.debug(f"开始预处理Node.js代码 - 代码长度: {len(code)}")
        processed_code = code

        # 使用AST插件系统转换代码
        try:
            context = {"language": "nodejs", "security_warnings": True}
            processed_code = nodejs_ast_manager.transform_code(
                processed_code, context
            )
            if runtime_config.debug_mode:
                logger.debug(
                    f"Node.js代码预处理完成 - 转换后长度: {len(processed_code)}"
                )
        except Exception as e:
            # 如果AST转换失败，继续使用原始代码
            logger.warning(f"AST转换失败，使用原始代码: {e}")
            print(f"AST转换失败，使用原始代码: {e}")

        return processed_code

    def get_command(self, filename: str = None) -> List[str]:
        """获取Node.js执行命令"""
        return [runtime_config.get_nodejs_command()]

    def _setup_seccomp_security(self):
        """在子进程中设置seccomp安全限制"""
        # 检查是否启用了seccomp
        try:
            if runtime_config.debug_mode:
                logger.debug("开始设置Node.js seccomp安全限制")
            # 使用安全管理器设置seccomp过滤器
            create_secure_process(
                language="nodejs",
                uid=runtime_config.sandbox_uid,
                gid=runtime_config.sandbox_gid,
                library_dir=runtime_config.nodejs_security_lib_dir,
            )
            if runtime_config.debug_mode:
                logger.debug("Node.js seccomp安全限制设置成功")
        except Exception as e:
            # 如果seccomp设置失败，记录错误但继续执行
            logger.error(f"Node.js seccomp安全设置失败: {e}")
            print(f"seccomp安全设置失败: {e}", file=sys.stderr)

    def execute(
        self,
        code: str,
        input_data: str = "",
        env_vars: Dict[str, str] | None = None,
    ) -> ExecutionResult:
        """执行Node.js代码"""
        start_time = time.time()
        if runtime_config.debug_mode:
            logger.debug(
                f"开始执行Node.js代码 - 代码长度: {len(code)} - 输入长度: {len(input_data)}"
            )

        # 预处理代码
        try:
            processed_code = self.preprocess_code(code)
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Node.js代码预处理失败 - 错误: {e} - 耗时: {execution_time:.3f}s"
            )
            error_msg = (
                f"Node.js代码预处理失败: {str(e)}\n{traceback.format_exc()}"
            )
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                stdout="",
                stderr=error_msg,
                execution_time=execution_time,
                exit_code=-1,
                error_message=error_msg,
            )

        # 使用上下文管理器创建临时沙盒目录
        with temporary_sandbox_dir() as sandbox_dir:
            if runtime_config.debug_mode:
                logger.debug(f"创建Node.js临时沙盒目录: {sandbox_dir}")

            try:
                # 创建加密工具实例
                crypto_utils = CryptoUtils()

                # 生成加密密钥并加密代码
                encryption_key = crypto_utils.generate_encryption_key()
                encrypted_code = crypto_utils.encrypt_code(
                    processed_code, encryption_key
                )
                if runtime_config.debug_mode:
                    logger.debug("Node.js代码加密完成")

                # 创建entrypoint文件（直接嵌入加密代码）
                entrypoint_path = create_file_in_dir(
                    sandbox_dir,
                    "entrypoint.js",
                    entrypoint_templates.create_entrypoint(
                        "nodejs",
                        encrypted_code,
                        encryption_key,
                        str(runtime_config.sandbox_uid),
                        str(runtime_config.sandbox_gid),
                    ),
                )

                # 设置执行权限
                set_executable_permission(entrypoint_path)
                if runtime_config.debug_mode:
                    logger.debug(
                        f"创建Node.js entrypoint文件: {entrypoint_path}"
                    )

                # 构建执行命令（只传递加密密钥）
                node_command = self.get_command()
                command = node_command + [entrypoint_path, encryption_key]
                if runtime_config.debug_mode:
                    logger.debug(f"Node.js执行命令: {' '.join(command)}")

                # 传递基本的环境变量，包括PATH
                process_env = {"PATH": os.environ.get("PATH", "")}

                # 执行进程，在preexecfn中设置seccomp安全限制
                process = subprocess.Popen(  # nosec B603
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
                    timeout=runtime_config.code_execution_timeout,
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
                logger.warning(
                    f"Node.js代码执行超时 - 耗时: {execution_time:.3f}s"
                )
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
                logger.error(
                    f"Node.js代码执行异常 - 错误: {e} - 耗时: {execution_time:.3f}s"
                )
                error_msg = (
                    f"Node.js代码执行异常: {str(e)}\n{traceback.format_exc()}"
                )
                return ExecutionResult(
                    status=ExecutionStatus.ERROR,
                    stdout="",
                    stderr=error_msg,
                    execution_time=execution_time,
                    exit_code=-1,
                    error_message=error_msg,
                )
