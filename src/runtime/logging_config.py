"""
日志配置模块
统一配置日志格式和级别
"""

import logging
import sys
from typing import Optional

from src.config import runtime_config


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """设置日志配置"""

    # 确定日志级别
    if level is None:
        level = "info"

    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=_get_handlers(log_file),
        force=True,  # 强制重新配置
    )


def _get_handlers(log_file: Optional[str] = None) -> list:
    """获取日志处理器"""
    handlers = []

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # 控制台只显示INFO及以上
    console_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    # 文件处理器（如果指定了日志文件）
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    return handlers


def get_logger(name: str) -> logging.Logger:
    """获取日志器实例"""
    return logging.getLogger(name)


# 在模块加载时设置默认日志配置
if not runtime_config.test_mode:
    setup_logging()
