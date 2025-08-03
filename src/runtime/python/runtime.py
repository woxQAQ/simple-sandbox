import os
import subprocess  # nosec B404
import time
from typing import Dict, List

from src.config import runtime_config
from src.models import ExecutionResult, ExecutionStatus
from src.runtime.common.base import LanguageRuntime
from src.runtime.common.runtime_utils import RuntimeUtils
from src.runtime.logging_config import create_runtime_logger
from src.runtime.python.extensions import PythonASTContext, python_ast_registry
from src.security import create_secure_process
from src.utils import temporary_sandbox_dir

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

            final_code = transformed_code
            logger.debug(f"代码预处理完成 - 转换后长度: {len(final_code)}")
            return final_code
        except Exception as e:
            logger.error(f"代码预处理失败 - 错误: {e}")
            raise

    def get_command(self, filename: str = None) -> List[str]:
        """获取Python执行命令"""
        return [runtime_config.get_python_command()]

    def _setup_filesystem_isolation(self, sandbox_dir):
        """设置文件系统隔离"""
        try:
            if runtime_config.debug_mode:
                logger.debug(f"开始设置文件系统隔离，沙盒目录: {sandbox_dir}")

            current_uid = os.getuid()
            current_gid = os.getgid()

            if runtime_config.debug_mode:
                logger.debug(
                    f"当前进程权限 - UID: {current_uid}, GID: {current_gid}"
                )

            # 设置环境变量限制文件系统访问
            os.environ["PYTHONPATH"] = sandbox_dir
            os.environ["HOME"] = sandbox_dir
            os.environ["TMPDIR"] = sandbox_dir

            # 限制当前目录到沙盒目录
            os.chdir(sandbox_dir)

            # 设置权限
            if current_uid == 0:
                # 如果是root用户，降权到sandbox用户
                os.setgid(runtime_config.sandbox_gid)
                os.setuid(runtime_config.sandbox_uid)

                if runtime_config.debug_mode:
                    logger.debug(
                        f"权限降权完成 - UID: {os.getuid()}, GID: {os.getgid()}"
                    )
            else:
                # 非root用户，设置NO_NEW_PRIVS
                try:
                    import ctypes

                    libc = ctypes.CDLL("libc.so.6")
                    result = libc.prctl(38, 1, 0, 0, 0)
                    if runtime_config.debug_mode:
                        logger.debug(f"PR_SET_NO_NEW_PRIVS设置结果: {result}")
                except Exception as e:
                    if runtime_config.debug_mode:
                        logger.debug(f"PR_SET_NO_NEW_PRIVS设置失败: {e}")

            if runtime_config.debug_mode:
                logger.debug("文件系统隔离设置完成")

        except Exception as e:
            if runtime_config.debug_mode:
                logger.debug(f"文件系统隔离设置失败: {e}")
            # 文件系统隔离失败时，记录错误但继续执行
            return

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
                logger.debug(
                    f"当前进程权限 - UID: {current_uid}, GID: {current_gid}"
                )
                logger.debug(
                    f"目标权限 - UID: {runtime_config.sandbox_uid}, GID: {runtime_config.sandbox_gid}"
                )

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
                        logger.debug(
                            "非root用户运行，跳过seccomp设置但设置NO_NEW_PRIVS"
                        )

                    # 设置PR_SET_NO_NEW_PRIVS以增强安全性
                    try:
                        import ctypes

                        libc = ctypes.CDLL("libc.so.6")
                        result = libc.prctl(38, 1, 0, 0, 0)
                        if runtime_config.debug_mode:
                            logger.debug(
                                f"PR_SET_NO_NEW_PRIVS设置结果: {result}"
                            )
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
            return RuntimeUtils.create_preprocess_error(e, execution_time)

        # 使用上下文管理器创建临时沙盒目录
        with temporary_sandbox_dir() as sandbox_dir:
            if runtime_config.debug_mode:
                logger.debug(f"创建临时沙盒目录: {sandbox_dir}")

            try:
                # 使用公共工具加密代码
                encrypted_code, encryption_key = RuntimeUtils.encrypt_code(
                    processed_code
                )

                # 获取seccomp库路径
                seccomp_lib_path = RuntimeUtils.get_seccomp_lib_path("python")

                # 创建entrypoint文件
                entrypoint_path = RuntimeUtils.create_entrypoint_file(
                    sandbox_dir,
                    "python",
                    encrypted_code,
                    encryption_key,
                    seccomp_lib_path,
                )

                # 构建执行命令
                command = [
                    runtime_config.get_python_command(),
                    entrypoint_path,
                    encryption_key,
                ]

                # 设置进程环境变量
                process_env = RuntimeUtils.setup_process_environment()

                # 执行进程，在preexecfn中设置安全限制
                def setup_security():
                    # 首先设置文件系统隔离
                    self._setup_filesystem_isolation(sandbox_dir)
                    # 然后设置seccomp安全限制
                    self._setup_seccomp_security()

                process = subprocess.Popen(  # nosec B603
                    command,
                    stdin=subprocess.PIPE if input_data else None,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=process_env,
                    text=True,
                    cwd=sandbox_dir,
                    preexec_fn=setup_security,
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
                    exit_code=process.returncode,
                    error_message=stderr if process.returncode != 0 else None,
                )

                # 记录执行结果日志
                RuntimeUtils.log_execution_result(
                    "Python", result, execution_time
                )

                return result

            except subprocess.TimeoutExpired:
                execution_time = time.time() - start_time
                return RuntimeUtils.create_timeout_error(execution_time)

            except Exception as e:
                execution_time = time.time() - start_time
                return RuntimeUtils.create_execution_error(
                    "执行异常", str(e), execution_time
                )
