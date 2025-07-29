#!/usr/bin/env python3
"""
代码沙箱服务器主程序
"""

import argparse
import logging
import sys

from src.api.app import run_server


def setup_logging(level=logging.INFO):
    """设置日志配置"""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="代码沙箱HTTP服务器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 使用默认端口8000
  %(prog)s --port 8080        # 使用端口8080
  %(prog)s -p 9000 -v         # 使用端口9000并启用详细日志
        """,
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="服务器监听端口 (默认: 8000)",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="服务器监听地址 (默认: 0.0.0.0)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="启用详细日志输出"
    )

    parser.add_argument("--debug", action="store_true", help="启用调试模式")

    args = parser.parse_args()

    # 设置日志级别
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    setup_logging(log_level)

    logger = logging.getLogger(__name__)

    # 显示启动信息
    logger.info("启动代码沙箱服务器")
    logger.info(f"监听地址: {args.host}")
    logger.info(f"监听端口: {args.port}")
    logger.info(f"日志级别: {logging.getLevelName(log_level)}")

    try:
        # 启动服务器
        run_server(host=args.host, port=args.port)
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
