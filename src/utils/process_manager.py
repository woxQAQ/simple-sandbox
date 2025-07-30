import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional

from src.models import ExecutionResult, ExecutionStatus
from src.security import SecurityError, SecurityManager

logger = logging.getLogger(__name__)


class ProcessManager:
    """子进程管理器，用于执行外部进程代码"""

    def __init__(
        self, work_dir: str = "/tmp/sandbox", enable_security: bool = True
    ):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # 安全相关设置
        self.enable_security = enable_security
        self.security_manager = SecurityManager() if enable_security else None

        # 默认的安全用户/组ID（使用nobody用户）
        self.secure_uid = 65534  # nobody
        self.secure_gid = 65534  # nogroup

    def execute(
        self,
        command: List[str],
        code: str,
        input_data: str = "",
        env_vars: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        language: str = "python",
    ) -> ExecutionResult:
        """使用子进程执行代码"""
        start_time = time.time()
        temp_filename = None

        try:
            # 创建临时文件
            temp_filename = self._create_temp_file(code, command[0])

            # 准备环境变量
            process_env = self._prepare_environment(env_vars, input_data)

            # 构建完整命令
            full_command = command + [temp_filename]

            # 执行进程
            stdout, stderr, exit_code = self._run_subprocess(
                full_command, process_env, input_data, timeout, language
            )

            execution_time = time.time() - start_time
            status = self._determine_status(exit_code, stderr)

            return ExecutionResult(
                status=status,
                stdout=stdout or "",
                stderr=stderr or "",
                execution_time=execution_time,
                memory_used_mb=0.0,
                exit_code=exit_code,
                error_message=stderr if exit_code != 0 else None,
            )

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                stdout="",
                stderr="Execution timed out",
                execution_time=execution_time,
                memory_used_mb=0.0,
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
                memory_used_mb=0.0,
                exit_code=-1,
                error_message=str(e),
            )

        finally:
            # 清理临时文件
            if temp_filename:
                self._cleanup_temp_file(temp_filename)

    def _create_temp_file(self, code: str, language: str) -> str:
        """创建临时文件"""
        # 根据语言确定文件后缀
        suffix_map = {
            "python": ".py",
            "node": ".js",
            "nodejs": ".js",
        }
        suffix = suffix_map.get(language, f".{language}")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, dir=self.work_dir
        ) as f:
            f.write(code)
            return f.name

    def _prepare_environment(
        self, env_vars: Optional[Dict[str, str]], input_data: str
    ) -> Dict[str, str]:
        """准备环境变量"""
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # 添加输入数据到环境变量
        if input_data:
            env["PROCESS_INPUT"] = input_data

        return env

    def _run_subprocess(
        self,
        command: List[str],
        env: Dict[str, str],
        input_data: str,
        timeout: Optional[float],
        language: str,
    ) -> tuple[str, str, int]:
        """运行子进程"""

        # 应用安全策略
        def preexec_fn():
            if self.enable_security and self.security_manager:
                self._apply_security_policies(language)

        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE if input_data else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            cwd=self.work_dir,
            preexec_fn=preexec_fn,
        )

        stdout, stderr = process.communicate(
            input=input_data if input_data else None,
            timeout=timeout,
        )

        return stdout, stderr, process.returncode

    def _determine_status(self, exit_code: int, stderr: str) -> ExecutionStatus:
        """根据退出码和错误信息确定状态"""
        if exit_code == 0:
            return ExecutionStatus.SUCCESS
        else:
            return ExecutionStatus.ERROR

    def _cleanup_temp_file(self, filename: str):
        """清理临时文件"""
        try:
            os.unlink(filename)
        except OSError:
            pass

    def _apply_security_policies(self, language: str):
        """应用安全策略"""
        if not self.security_manager:
            return

        try:
            # 检查seccomp是否支持
            if not self.security_manager.is_seccomp_supported():
                logger.info("当前平台不支持seccomp，跳过安全策略应用")
                return

            # 应用完整的安全配置
            self.security_manager.setup_security_profile(
                language, self.secure_uid, self.secure_gid
            )
            logger.info(f"已为 {language} 运行时应用安全策略")
        except SecurityError as e:
            # 如果安全策略应用失败，记录错误但不中断执行
            logger.warning(f"安全策略应用失败: {e}")
        except Exception as e:
            logger.warning(f"安全策略应用时发生意外错误: {e}")
            # 记录更详细的错误信息用于调试
            import traceback

            logger.debug(f"安全策略应用失败详情: {traceback.format_exc()}")

    def cleanup(self):
        """清理资源"""
        # 目前不需要特别清理，临时文件会在执行后自动删除
        pass
