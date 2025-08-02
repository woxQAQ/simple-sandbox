import os
import subprocess  # nosec B404
import time
import traceback
from typing import Dict, List

from src.config import runtime_config
from src.runtime.common.base import LanguageRuntime
from src.runtime.common.models import ExecutionResult, ExecutionStatus
from src.runtime.logging_config import create_runtime_logger
from src.runtime.python.extensions import PythonASTContext, python_ast_registry
from src.security import create_secure_process
from src.utils import (
    create_file_in_dir,
    entrypoint_templates,
    set_executable_permission,
    temporary_sandbox_dir,
)
from src.utils.crypto_utils import CryptoUtils

logger = create_runtime_logger(__name__)


class PythonRuntime(LanguageRuntime):
    """Python运行时实现"""

    def __init__(self):
        super().__init__("python")

    def get_supported_extensions(self) -> List[str]:
        return [".py", ".pyw"]

    def preprocess_code(
        self, code: str, input_data: str = "", env_vars: Dict[str, str] = None
    ) -> str:
        """使用扩展系统预处理Python代码"""
        logger.debug(f"开始预处理Python代码 - 代码长度: {len(code)}")

        # 创建AST上下文
        context = PythonASTContext(source_code=code)

        # 使用插件系统转换代码
        try:
            transformed_code = python_ast_registry.transform_code(code, context)
            logger.debug(
                f"代码预处理完成 - 转换后长度: {len(transformed_code)}"
            )
            return transformed_code
        except Exception as e:
            logger.error(f"代码预处理失败 - 错误: {e}")
            raise

    def get_command(self, filename: str = None) -> List[str]:
        """获取Python执行命令"""
        return [runtime_config.get_python_command()]

    def _setup_seccomp_security(self):
        """在子进程中设置seccomp安全限制"""
        # 检查是否启用了seccomp
        try:
            if runtime_config.debug_mode:
                logger.debug("开始设置seccomp安全限制")

            # 使用安全管理器设置seccomp过滤器
            create_secure_process(
                language="python",
                uid=runtime_config.sandbox_uid,
                gid=runtime_config.sandbox_gid,
                library_dir=runtime_config.python_security_lib_dir,
            )
            if runtime_config.debug_mode:
                logger.debug("seccomp安全限制设置成功")
        except Exception as e:
            # seccomp设置失败时，静默处理
            # 在preexec_fn中不应该输出到stderr，因为这会污染用户代码的输出
            # 但是为了调试，我们可以输出到文件
            if runtime_config.debug_mode:
                with open("/tmp/seccomp_debug.log", "a") as f:
                    f.write(f"seccomp设置失败: {e}\n")
            pass

    def execute(
        self,
        code: str,
        input_data: str = "",
        env_vars: Dict[str, str] | None = None,
    ) -> ExecutionResult:
        """执行Python代码"""
        start_time = time.time()

        # 预处理代码
        try:
            processed_code = self.preprocess_code(code, input_data, env_vars)
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"代码预处理失败 - 错误: {e} - 耗时: {execution_time:.3f}s"
            )
            error_msg = f"代码预处理失败: {str(e)}\\n{traceback.format_exc()}"
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
                logger.debug(f"创建临时沙盒目录: {sandbox_dir}")

            try:
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
                        "python",
                        encrypted_code,
                        encryption_key,
                        str(runtime_config.sandbox_uid),
                        str(runtime_config.sandbox_gid),
                        runtime_config.python_security_lib_dir
                        + "/libseccomp_injector_python.so",
                    ),
                )

                # 设置执行权限
                set_executable_permission(entrypoint_path)

                # 构建执行命令（只传递加密密钥）
                command = [
                    runtime_config.get_python_command(),
                    entrypoint_path,
                    encryption_key,
                ]

                # 传递基本的环境变量，包括PATH
                process_env = {"PATH": os.environ.get("PATH", "")}

                # 执行进程，暂时不使用preexecfn避免子进程创建失败
                process = subprocess.Popen(  # nosec B603
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
                    timeout=runtime_config.code_execution_timeout,
                )

                execution_time = time.time() - start_time

                logger.info(
                    f"Python代码执行完成 - 状态: {process.returncode} - "
                    f"执行时间: {execution_time:.3f}s - "
                    f"stdout长度: {len(stdout)} - stderr长度: {len(stderr)}"
                )

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
                    f"Python代码执行超时 - 耗时: {execution_time:.3f}s"
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
                    f"Python代码执行异常 - 错误: {e} - 耗时: {execution_time:.3f}s"
                )
                error_msg = (
                    f"Python代码执行异常: {str(e)}\\n{traceback.format_exc()}"
                )
                return ExecutionResult(
                    status=ExecutionStatus.ERROR,
                    stdout="",
                    stderr=error_msg,
                    execution_time=execution_time,
                    exit_code=-1,
                    error_message=error_msg,
                )
