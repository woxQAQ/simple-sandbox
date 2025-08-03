"""
项目配置模块
"""

import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


# 加载 .env 文件
def load_env_file():
    """加载环境变量配置文件"""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # 如果项目根目录没有 .env 文件，尝试加载示例文件
        example_env_file = Path(__file__).parent.parent / ".env.example"
        if example_env_file.exists():
            load_dotenv(example_env_file)


# 在模块加载时自动加载环境变量
load_env_file()


class RuntimeConfig:
    """运行时配置类"""

    def __init__(self):
        # 基础路径配置
        self.base_dir = Path(__file__).parent
        self.runtime_dir = self.base_dir / "runtime"

        # 语言运行时路径
        self.python_runtime_dir = self.runtime_dir / "python"
        self.nodejs_runtime_dir = self.runtime_dir / "nodejs"

        # Transformer路径（仅Python支持transformer）
        self.python_transformer_path = (
            self.python_runtime_dir / "transformer.py"
        )
        # Node.js不再支持transformer

        # 插件路径
        self.python_plugins_dir = self.python_runtime_dir / "plugins"
        self.nodejs_plugins_dir = self.nodejs_runtime_dir / "plugins"

        # 安全库路径
        self.python_security_lib_dir = "/var/sandbox/python"
        self.nodejs_security_lib_dir = "/var/sandbox/nodejs"

        # 用户ID和组ID
        self.sandbox_uid = int(os.getenv("SANDBOX_USER_ID", "1000"))
        self.sandbox_gid = int(os.getenv("SANDBOX_GROUP_ID", "1000"))

        # 执行超时时间
        self.transformer_timeout = int(os.getenv("TRANSFORMER_TIMEOUT", "10"))
        self.code_execution_timeout = int(
            os.getenv("CODE_EXECUTION_TIMEOUT", "30")
        )

        # 调试模式
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

        # 测试模式
        self.test_mode = os.getenv("TEST_MODE", "false").lower() == "true"

        # 如果是测试模式，使用测试路径
        if self.test_mode:
            self._setup_test_paths()

    def _setup_test_paths(self):
        """设置测试模式下的路径"""
        # 在测试模式下，使用相对于当前工作目录的路径
        current_dir = Path.cwd()
        self.runtime_dir = current_dir / "src" / "runtime"
        self.python_runtime_dir = self.runtime_dir / "python"
        self.nodejs_runtime_dir = self.runtime_dir / "nodejs"
        self.python_transformer_path = (
            self.python_runtime_dir / "transformer.py"
        )
        # Node.js不再支持transformer
        self.python_plugins_dir = self.python_runtime_dir / "plugins"
        self.nodejs_plugins_dir = self.nodejs_runtime_dir / "plugins"

        # 检查是否在Docker容器中
        if os.path.exists("/var/sandbox"):
            # 在Docker容器中，使用容器内的安全库路径
            self.python_security_lib_dir = "/var/sandbox/python"
            self.nodejs_security_lib_dir = "/var/sandbox/nodejs"
        else:
            # 在开发环境中，使用build目录作为安全库路径
            build_lib_dir = self.base_dir.parent / "build" / "lib"
            self.python_security_lib_dir = str(build_lib_dir)
            self.nodejs_security_lib_dir = str(build_lib_dir)

    def get_python_command(self) -> str:
        """获取Python命令"""
        if self.test_mode:
            return "python3"
        return os.getenv("PYTHON_PATH", "python3")

    def get_nodejs_command(self) -> str:
        """获取Node.js命令"""
        if self.test_mode:
            return "node"
        return os.getenv("NODEJS_PATH", "node")

    def get_python_transformer_command(self) -> list:
        """获取Python transformer命令"""
        return [self.get_python_command(), str(self.python_transformer_path)]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "base_dir": str(self.base_dir),
            "runtime_dir": str(self.runtime_dir),
            "python_runtime_dir": str(self.python_runtime_dir),
            "nodejs_runtime_dir": str(self.nodejs_runtime_dir),
            "python_transformer_path": str(self.python_transformer_path),
            # Node.js不再支持transformer
            "python_plugins_dir": str(self.python_plugins_dir),
            "nodejs_plugins_dir": str(self.nodejs_plugins_dir),
            "python_security_lib_dir": self.python_security_lib_dir,
            "nodejs_security_lib_dir": self.nodejs_security_lib_dir,
            "sandbox_uid": self.sandbox_uid,
            "sandbox_gid": self.sandbox_gid,
            "transformer_timeout": self.transformer_timeout,
            "code_execution_timeout": self.code_execution_timeout,
            "debug_mode": self.debug_mode,
            "test_mode": self.test_mode,
            "python_command": self.get_python_command(),
            "nodejs_command": self.get_nodejs_command(),
        }


class Config:
    """项目配置类"""

    # 运行时路径配置
    PYTHON_PATH = os.getenv("PYTHON_PATH", "python3")
    NODEJS_PATH = os.getenv("NODEJS_PATH", "node")

    # 并发控制配置
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "100"))

    # 超时配置
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # 秒
    CODE_EXECUTION_TIMEOUT = int(
        os.getenv("CODE_EXECUTION_TIMEOUT", "30")
    )  # 秒

    # 安全配置
    ENABLE_RATE_LIMITING = (
        os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    )
    ENABLE_REQUEST_TIMEOUT = (
        os.getenv("ENABLE_REQUEST_TIMEOUT", "true").lower() == "true"
    )

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "PYTHON_PATH": cls.PYTHON_PATH,
            "NODEJS_PATH": cls.NODEJS_PATH,
            "MAX_CONCURRENT_REQUESTS": cls.MAX_CONCURRENT_REQUESTS,
            "MAX_REQUESTS_PER_MINUTE": cls.MAX_REQUESTS_PER_MINUTE,
            "REQUEST_TIMEOUT": cls.REQUEST_TIMEOUT,
            "CODE_EXECUTION_TIMEOUT": cls.CODE_EXECUTION_TIMEOUT,
            "ENABLE_RATE_LIMITING": cls.ENABLE_RATE_LIMITING,
            "ENABLE_REQUEST_TIMEOUT": cls.ENABLE_REQUEST_TIMEOUT,
        }


# 全局配置实例
config = Config()
runtime_config = RuntimeConfig()


def get_test_config() -> RuntimeConfig:
    """获取测试配置"""
    # 设置测试环境变量
    os.environ["TEST_MODE"] = "true"
    os.environ["DEBUG_MODE"] = "true"
    os.environ["TRANSFORMER_TIMEOUT"] = "5"
    os.environ["CODE_EXECUTION_TIMEOUT"] = "10"

    return RuntimeConfig()
