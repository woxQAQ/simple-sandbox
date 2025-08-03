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

            # 在容器环境中，检查当前用户权限
            current_uid = os.getuid()
            current_gid = os.getgid()
            
            if runtime_config.debug_mode:
                logger.debug(f"当前进程权限 - UID: {current_uid}, GID: {current_gid}")
                logger.debug(f"目标权限 - UID: {runtime_config.sandbox_uid}, GID: {runtime_config.sandbox_gid}")

            # 使用安全管理器设置seccomp过滤器
            # 在开发环境中使用构建输出目录
            if os.path.exists("/var/sandbox"):
                actual_lib_dir = "/var/sandbox"
                
                # 在容器环境中，只有root用户才能设置seccomp
                if current_uid == 0:
                    # 以root用户运行，可以设置seccomp
                    create_secure_process(
                        language="python",
                        uid=runtime_config.sandbox_uid,
                        gid=runtime_config.sandbox_gid,
                        library_dir=actual_lib_dir,
                    )
                    if runtime_config.debug_mode:
                        logger.debug("seccomp安全限制设置成功")
                else:
                    # 以非root用户运行，跳过seccomp设置但设置NO_NEW_PRIVS
                    if runtime_config.debug_mode:
                        logger.debug("非root用户运行，跳过seccomp设置但设置NO_NEW_PRIVS")
                    
                    # 设置PR_SET_NO_NEW_PRIVS以增强安全性
                    try:
                        import ctypes
                        libc = ctypes.CDLL('libc.so.6')
                        # PR_SET_NO_NEW_PRIVS = 38
                        result = libc.prctl(38, 1, 0, 0, 0)
                        if runtime_config.debug_mode:
                            logger.debug(f"PR_SET_NO_NEW_PRIVS设置结果: {result}")
                    except Exception as e:
                        if runtime_config.debug_mode:
                            logger.debug(f"PR_SET_NO_NEW_PRIVS设置失败: {e}")
            else:
                # 开发环境中跳过seccomp设置
                if runtime_config.debug_mode:
                    logger.debug("开发环境中跳过seccomp设置")
                return
        except Exception as e:
            # seccomp设置失败时，记录错误但继续执行
            # 这样可以确保代码在没有seccomp保护的情况下仍能运行
            error_msg = f"seccomp安全限制设置失败: {e}"
            logger.error(error_msg)
            # 不再抛出异常，允许进程继续执行
            return

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
                # 使用Docker容器中的标准库路径
                if os.path.exists("/var/sandbox"):
                    seccomp_lib_path = (
                        "/var/sandbox/python/libseccomp_injector_python.so"
                    )
                else:
                    # 开发环境路径
                    seccomp_lib_path = os.path.join(
                        os.path.dirname(__file__),
                        "..",
                        "..",
                        "..",
                        "build",
                        "lib",
                        "libseccomp_injector_python.so",
                    )

                # 检查seccomp库是否存在，如果不存在则跳过seccomp设置
                if not os.path.exists(seccomp_lib_path):
                    if runtime_config.debug_mode:
                        logger.debug(
                            f"seccomp库文件不存在: {seccomp_lib_path}，跳过seccomp设置"
                        )
                    seccomp_lib_path = None

                entrypoint_path = create_file_in_dir(
                    sandbox_dir,
                    "entrypoint.py",
                    entrypoint_templates.create_entrypoint(
                        "python",
                        encrypted_code,
                        encryption_key,
                        str(runtime_config.sandbox_uid),
                        str(runtime_config.sandbox_gid),
                        seccomp_lib_path,
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

                # 记录详细的执行结果
                if process.returncode == 0:
                    logger.info(
                        f"Python代码执行成功 - 状态: {process.returncode} - "
                        f"执行时间: {execution_time:.3f}s - "
                        f"stdout长度: {len(stdout)} - stderr长度: {len(stderr)}"
                    )
                else:
                    logger.warning(
                        f"Python代码执行失败 - 状态: {process.returncode} - "
                        f"执行时间: {execution_time:.3f}s - "
                        f"stdout长度: {len(stdout)} - stderr长度: {len(stderr)} - "
                        f"stderr: {stderr[:200]}{'...' if len(stderr) > 200 else ''}"
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
