"""
临时沙盒目录管理模块
提供上下文管理器来管理临时目录的创建和清理
"""

import os
import shutil
import tempfile
from contextlib import contextmanager
from typing import Generator


@contextmanager
def temporary_sandbox_dir() -> Generator[str, None, None]:
    """临时沙盒目录上下文管理器"""
    temp_dir = None
    try:
        # 创建临时目录 - 使用系统临时目录
        temp_dir = tempfile.mkdtemp(prefix="sandbox_")
        os.chmod(temp_dir, 0o700)
        yield temp_dir
    finally:
        # 自动清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                # 忽略清理错误 - 临时目录清理失败不影响功能
                # nosec B110 - cleanup failures are intentionally ignored
                pass


def create_file_in_dir(directory: str, filename: str, content: str) -> str:
    """在指定目录中创建文件"""
    file_path = os.path.join(directory, filename)
    with open(file_path, "w") as f:
        f.write(content)
    return file_path


def set_executable_permission(file_path: str):
    """设置文件可执行权限"""
    os.chmod(file_path, 0o700)
