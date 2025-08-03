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
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """设置日志配置"""

    # 确定日志级别
    if level is None:
        if runtime_config.debug_mode:
            level = "DEBUG"
        elif runtime_config.test_mode:
            level = "INFO"
        else:
            level = "WARNING"

    # 设置日志格式
    if format_string is None:
        if runtime_config.debug_mode:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        else:
            format_string = (
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
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


# 日志级别常量
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"


class RuntimeLogger:
    """运行时日志器包装类，提供简化的日志接口"""

    def __init__(self, name: str):
        self.logger = get_logger(name)
        self.debug_mode = runtime_config.debug_mode

    def debug(self, message: str, *args, **kwargs) -> None:
        """调试日志 - 只在调试模式下输出"""
        if self.debug_mode:
            self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """信息日志 - 关键步骤信息"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """警告日志 - 警告信息"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """错误日志 - 错误信息"""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """严重错误日志 - 严重错误信息"""
        self.logger.critical(message, *args, **kwargs)


def create_runtime_logger(name: str) -> RuntimeLogger:
    """创建运行时日志器"""
    return RuntimeLogger(name)


# 在模块加载时设置默认日志配置
if not runtime_config.test_mode:
    setup_logging()
