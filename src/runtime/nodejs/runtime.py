import os
import subprocess  # nosec B404
import time
from typing import Dict, List

from src.config import runtime_config
from src.models import ExecutionResult, ExecutionStatus
from src.runtime.common.base import LanguageRuntime
from src.runtime.common.runtime_utils import RuntimeUtils
from src.runtime.logging_config import create_runtime_logger
from src.runtime.nodejs.extensions import nodejs_ast_manager
from src.security import create_secure_process
from src.utils import temporary_sandbox_dir

logger = create_runtime_logger(__name__)


class NodeJSRuntime(LanguageRuntime):
    """Node.js运行时实现"""

    def __init__(self):
        super().__init__("nodejs")

    def get_supported_extensions(self) -> List[str]:
        return [".js", ".mjs", ".cjs"]

    def preprocess_code(self, code: str) -> str:
        """预处理Node.js代码（已移除transformer功能）"""
        if runtime_config.debug_mode:
            logger.debug(f"开始预处理Node.js代码 - 代码长度: {len(code)}")
        
        # 直接返回原始代码，不再使用AST转换
        processed_code = code
        
        if runtime_config.debug_mode:
            logger.debug(
                f"Node.js代码预处理完成 - 长度: {len(processed_code)}"
            )
        
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
            # 在新的沙盒目录中，seccomp库位于当前目录
            if os.path.exists("/var/sandbox"):
                # 在Docker容器环境中启用seccomp
                # 库路径设置为当前目录，因为seccomp库已经复制到沙盒目录
                create_secure_process(
                    language="nodejs",
                    uid=runtime_config.sandbox_uid,
                    gid=runtime_config.sandbox_gid,
                    library_dir=".",  # 使用当前目录
                )
            else:
                # 开发环境中跳过seccomp设置
                if runtime_config.debug_mode:
                    logger.debug("开发环境中跳过seccomp设置")
                return
            if runtime_config.debug_mode:
                logger.debug("Node.js seccomp安全限制设置成功")
        except Exception:
            # seccomp设置失败时，静默处理
            # 在preexec_fn中不应该输出到stderr，因为这会污染用户代码的输出
            pass

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
            return RuntimeUtils.create_preprocess_error(e, execution_time)

        # 使用新的Node.js沙盒目录管理器
        with RuntimeUtils.nodejs_sandbox_dir() as sandbox_dir:
            if runtime_config.debug_mode:
                logger.debug(f"使用Node.js沙盒目录: {sandbox_dir}")

            try:
                # 使用公共工具加密代码
                encrypted_code, encryption_key = RuntimeUtils.encrypt_code(
                    processed_code
                )

                # 获取seccomp库路径（在沙盒目录中）
                seccomp_lib_path = os.path.join(sandbox_dir, "libseccomp_injector_nodejs.so")

                # 创建entrypoint文件
                entrypoint_path = RuntimeUtils.create_entrypoint_file(
                    sandbox_dir,
                    "nodejs",
                    encrypted_code,
                    encryption_key,
                    seccomp_lib_path,
                )

                # 构建执行命令
                node_command = self.get_command()
                command = node_command + [entrypoint_path, encryption_key]
                if runtime_config.debug_mode:
                    logger.debug(f"Node.js执行命令: {' '.join(command)}")

                # 设置进程环境变量
                process_env = RuntimeUtils.setup_process_environment()

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
                    "Node.js", result, execution_time
                )

                return result

            except subprocess.TimeoutExpired:
                execution_time = time.time() - start_time
                # 确保进程被终止
                process.kill()
                process.wait()
                return RuntimeUtils.create_timeout_error(execution_time)

            except Exception as e:
                execution_time = time.time() - start_time
                return RuntimeUtils.create_execution_error(
                    "执行异常", str(e), execution_time
                )
