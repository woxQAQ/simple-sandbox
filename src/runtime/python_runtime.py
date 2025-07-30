import contextlib
import io
import os
import sys
import time
from typing import Dict, List

from src.runtime.base import LanguageRuntime
from src.runtime.extensions.python import PythonASTContext, python_ast_registry
from src.runtime.models import ExecutionResult, ExecutionStatus


class PythonRuntime(LanguageRuntime):
    """Python运行时实现"""

    def __init__(self):
        super().__init__("python")

    def get_supported_extensions(self) -> List[str]:
        return [".py", ".pyw"]

    def get_default_filename(self) -> str:
        return "main.py"

    def preprocess_code(
        self, code: str, input_data: str = "", env_vars: Dict[str, str] = None
    ) -> str:
        """使用扩展系统预处理Python代码"""
        # 创建AST上下文
        context = PythonASTContext(source_code=code)

        # 使用插件系统转换代码
        transformed_code = python_ast_registry.transform_code(code, context)
        return transformed_code

    def execute(
        self,
        code: str,
        input_data: str = "",
        env_vars: Dict[str, str] = None,
    ) -> ExecutionResult:
        """执行Python代码"""
        start_time = time.time()

        # 预处理代码
        processed_code = self.preprocess_code(code, input_data, env_vars)

        # 设置环境变量
        if env_vars is None:
            env_vars = {}

        # 临时保存当前环境变量
        old_env = {}
        for key, value in env_vars.items():
            old_env[key] = os.environ.get(key)
            os.environ[key] = value

        # 重定向标准输入输出
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        exit_code = 0
        error_message = None

        try:
            # 设置输入数据
            old_stdin = sys.stdin
            if input_data:
                sys.stdin = io.StringIO(input_data)

            # 执行代码
            with (
                contextlib.redirect_stdout(stdout_capture),
                contextlib.redirect_stderr(stderr_capture),
            ):
                # 创建一个命名空间来执行代码
                namespace = {
                    "__name__": "__main__",
                    "__file__": self.get_default_filename(),
                }

                try:
                    exec(processed_code, namespace)
                except SystemExit as e:
                    exit_code = e.code if e.code is not None else 0
                except Exception as e:
                    exit_code = 1
                    error_message = str(e)

        except Exception as e:
            exit_code = 1
            error_message = str(e)
        finally:
            # 恢复标准输入
            sys.stdin = old_stdin

            # 恢复环境变量
            for key in env_vars:
                if key in old_env:
                    if old_env[key] is not None:
                        os.environ[key] = old_env[key]
                    else:
                        os.environ.pop(key, None)

        # 获取输出
        stdout = stdout_capture.getvalue()
        stderr = stderr_capture.getvalue()

        # 计算执行时间
        execution_time = time.time() - start_time

        # 确定执行状态
        if error_message:
            status = ExecutionStatus.ERROR
        elif exit_code != 0:
            status = ExecutionStatus.ERROR
        else:
            status = ExecutionStatus.SUCCESS

        return ExecutionResult(
            status=status,
            stdout=stdout,
            stderr=stderr,
            execution_time=execution_time,
            memory_used_mb=0.0,
            exit_code=exit_code,
            error_message=error_message,
        )
