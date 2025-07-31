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
