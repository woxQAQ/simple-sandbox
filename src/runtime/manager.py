import os
import signal
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, List
import resource
import logging

from .models import ExecutionResult, ExecutionStatus

logger = logging.getLogger(__name__)


class ProcessManager:
    """进程管理器，负责创建和管理代码执行进程"""

    def __init__(self, work_dir: str = "/tmp/sandbox"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.active_processes: Dict[int, subprocess.Popen] = {}

    def execute_process(self, command: List[str], timeout: int, memory_limit: int,
                       stdin_data: str = "", env_vars: Dict[str, str] = None) -> ExecutionResult:
        """执行外部进程并管理资源"""

        # 创建临时工作目录
        with tempfile.TemporaryDirectory(dir=self.work_dir) as temp_dir:
            Path(temp_dir)  # Create Path object but don't assign to unused variable

            # 设置环境变量
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)

            # 设置资源限制
            def preexec_fn():
                try:
                    # 设置内存限制
                    resource.setrlimit(resource.RLIMIT_AS,
                                     (memory_limit * 1024 * 1024, memory_limit * 1024 * 1024))

                    # 设置CPU时间限制
                    resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))

                    # 设置进程数限制
                    resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))

                    # 设置文件大小限制
                    resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))

                    # 进入临时目录
                    os.chdir(temp_dir)

                except Exception as e:
                    logger.error(f"Error setting resource limits: {e}")

            start_time = time.time()

            try:
                # 创建进程
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=temp_dir,
                    env=env,
                    preexec_fn=preexec_fn
                )

                self.active_processes[process.pid] = process

                # 使用线程处理I/O避免阻塞
                stdout_data = ""
                stderr_data = ""

                def read_output():
                    nonlocal stdout_data, stderr_data
                    try:
                        stdout_data, stderr_data = process.communicate(
                            input=stdin_data, timeout=timeout
                        )
                    except subprocess.TimeoutExpired:
                        process.kill()
                        stdout_data, stderr_data = process.communicate()

                # 启动读取线程
                output_thread = threading.Thread(target=read_output)
                output_thread.start()
                output_thread.join(timeout=timeout + 2)  # 额外2秒缓冲

                if output_thread.is_alive():
                    # 超时处理
                    process.kill()
                    process.wait()
                    execution_time = time.time() - start_time

                    return ExecutionResult(
                        status=ExecutionStatus.TIMEOUT,
                        stdout=stdout_data,
                        stderr=stderr_data,
                        execution_time=execution_time,
                        memory_used_mb=0,
                        exit_code=-1,
                        error_message="Execution timeout"
                    )

                execution_time = time.time() - start_time
                exit_code = process.returncode

                # 检查退出状态
                if exit_code == 0:
                    status = ExecutionStatus.SUCCESS
                elif exit_code == -signal.SIGKILL:
                    status = ExecutionStatus.MEMORY_EXCEEDED
                elif exit_code == -signal.SIGXCPU:
                    status = ExecutionStatus.TIMEOUT
                else:
                    status = ExecutionStatus.ERROR

                return ExecutionResult(
                    status=status,
                    stdout=stdout_data,
                    stderr=stderr_data,
                    execution_time=execution_time,
                    memory_used_mb=0,  # TODO: 实现内存监控
                    exit_code=exit_code
                )

            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                execution_time = time.time() - start_time

                return ExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    stdout=stdout_data,
                    stderr=stderr_data,
                    execution_time=execution_time,
                    memory_used_mb=0,
                    exit_code=-1,
                    error_message="Process timeout"
                )

            except OSError as e:
                execution_time = time.time() - start_time
                return ExecutionResult(
                    status=ExecutionStatus.ERROR,
                    stdout="",
                    stderr=str(e),
                    execution_time=execution_time,
                    memory_used_mb=0,
                    exit_code=-1,
                    error_message=f"OS Error: {str(e)}"
                )

            finally:
                if process.pid in self.active_processes:
                    del self.active_processes[process.pid]

    def kill_process(self, pid: int) -> bool:
        """强制终止进程"""
        if pid in self.active_processes:
            try:
                process = self.active_processes[pid]
                process.kill()
                process.wait(timeout=5)
                del self.active_processes[pid]
                return True
            except (subprocess.TimeoutExpired, ProcessLookupError):
                return False
        return False

    def cleanup(self):
        """清理所有活动进程"""
        for pid in list(self.active_processes.keys()):
            self.kill_process(pid)
