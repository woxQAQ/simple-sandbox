"""项目配置模块"""

import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


def load_env_file():
    """加载环境变量配置文件"""
    # 首先检查项目根目录的 .env 文件
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        return

    # 然后检查 tests/e2e/ 目录的 .env 文件
    e2e_env_file = Path(__file__).parent.parent / "tests" / "e2e" / ".env"
    if e2e_env_file.exists():
        load_dotenv(e2e_env_file)
        return


load_env_file()


class RuntimeConfig:
    """运行时配置类"""

    def __init__(self):
        self.python_security_lib_dir = "/var/sandbox/python"
        self.nodejs_security_lib_dir = "/var/sandbox/nodejs"
        self.sandbox_uid = int(os.getenv("SANDBOX_USER_ID", "1000"))
        self.sandbox_gid = int(os.getenv("SANDBOX_GROUP_ID", "1000"))
        self.code_execution_timeout = int(
            os.getenv("CODE_EXECUTION_TIMEOUT", "30")
        )
        self.test_mode = os.getenv("TEST_MODE", "false").lower() == "true"

        if self.test_mode:
            self._setup_test_paths()

    def _setup_test_paths(self):
        """设置测试模式下的路径"""
        if os.path.exists("/var/sandbox"):
            self.python_security_lib_dir = "/var/sandbox/python"
            self.nodejs_security_lib_dir = "/var/sandbox/nodejs"
        else:
            build_lib_dir = Path(__file__).parent.parent / "build" / "lib"
            self.python_security_lib_dir = str(build_lib_dir)
            self.nodejs_security_lib_dir = str(build_lib_dir)

    def get_python_command(self) -> str:
        """获取Python命令"""
        return "python3" if self.test_mode else "python"

    def get_nodejs_command(self) -> str:
        """获取Node.js命令"""
        return "node" if self.test_mode else "node"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "python_security_lib_dir": self.python_security_lib_dir,
            "nodejs_security_lib_dir": self.nodejs_security_lib_dir,
            "sandbox_uid": self.sandbox_uid,
            "sandbox_gid": self.sandbox_gid,
            "code_execution_timeout": self.code_execution_timeout,
            "test_mode": self.test_mode,
            "python_command": self.get_python_command(),
            "nodejs_command": self.get_nodejs_command(),
        }


class Config:
    """项目配置类"""

    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "100"))
    ENABLE_RATE_LIMITING = (
        os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    )

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "MAX_CONCURRENT_REQUESTS": cls.MAX_CONCURRENT_REQUESTS,
            "MAX_REQUESTS_PER_MINUTE": cls.MAX_REQUESTS_PER_MINUTE,
            "ENABLE_RATE_LIMITING": cls.ENABLE_RATE_LIMITING,
        }


config = Config()
runtime_config = RuntimeConfig()


def get_test_config() -> RuntimeConfig:
    """获取测试配置"""
    os.environ["TEST_MODE"] = "true"
    os.environ["DEBUG_MODE"] = "true"
    os.environ["CODE_EXECUTION_TIMEOUT"] = "10"
    return RuntimeConfig()
