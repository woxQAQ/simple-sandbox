import os
import tempfile
from typing import Dict, List

from .base import LanguageRuntime
from .manager import ProcessManager
from .models import ExecutionResult


class PythonRuntime(LanguageRuntime):
    """Python运行时实现"""

    def __init__(self):
        super().__init__("python")
        self.process_manager = ProcessManager()

    def get_supported_extensions(self) -> List[str]:
        return [".py", ".pyw"]

    def get_default_filename(self) -> str:
        return "main.py"

    def preprocess_code(
        self, code: str, input_data: str = "", env_vars: Dict[str, str] = None
    ) -> str:
        """使用扩展系统预处理Python代码"""
        pass

    def get_command(self, filename: str) -> List[str]:
        """获取Python执行命令"""
        return ["python3", filename]

    def execute(
        self,
        code: str,
        timeout: int,
        memory_limit: int,
        input_data: str = "",
        env_vars: Dict[str, str] = None,
    ) -> ExecutionResult:
        """执行Python代码"""

        # 预处理代码
        processed_code = self.preprocess_code(code, input_data, env_vars)

        # 创建临时Python文件
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            dir=self.process_manager.work_dir,
            delete=False,
        ) as f:
            f.write(processed_code)
            temp_filename = f.name

        try:
            # 设置环境变量
            if env_vars is None:
                env_vars = {}

            # 添加输入数据作为命令行参数
            if input_data:
                env_vars["PYTHON_INPUT"] = input_data

            # 执行代码
            command = self.get_command(temp_filename)
            result = self.process_manager.execute_process(
                command=command,
                timeout=timeout,
                memory_limit=memory_limit,
                stdin_data=input_data,
                env_vars=env_vars,
            )

            return result

        finally:
            # 清理临时文件
            try:
                os.unlink(temp_filename)
            except OSError:
                pass
