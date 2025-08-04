"""
Node.js 运行时工具函数
"""

import os
import shutil
import uuid
from contextlib import contextmanager

from src.config import runtime_config
from src.runtime.logging_config import create_runtime_logger

logger = create_runtime_logger(__name__)


class NodeJSRuntimeUtils:
    """Node.js 运行时工具类"""

    @staticmethod
    @contextmanager
    def nodejs_sandbox_dir():
        """
        创建和管理Node.js沙盒目录的上下文管理器
        每次执行时创建/tmp/sandbox-[uuid]目录，并复制必要的安全库
        """
        # 创建唯一的沙盒目录
        sandbox_dir = f"/tmp/sandbox-{uuid.uuid4()}"

        try:
            # 创建沙盒目录
            os.makedirs(sandbox_dir, exist_ok=True)

            # 复制安全库和网络相关文件
            NodeJSRuntimeUtils._copy_nodejs_sandbox_files(sandbox_dir)

            if runtime_config.debug_mode:
                logger.debug(f"创建Node.js沙盒目录: {sandbox_dir}")

            yield sandbox_dir

        finally:
            # 清理沙盒目录
            try:
                if os.path.exists(sandbox_dir):
                    shutil.rmtree(sandbox_dir)
                    if runtime_config.debug_mode:
                        logger.debug(f"清理Node.js沙盒目录: {sandbox_dir}")
            except Exception as e:
                if runtime_config.debug_mode:
                    logger.debug(f"清理Node.js沙盒目录失败: {e}")

    @staticmethod
    def _copy_nodejs_sandbox_files(sandbox_dir: str):
        """
        复制Node.js沙盒所需的文件

        Args:
            sandbox_dir: 目标沙盒目录
        """
        # 需要复制的文件列表
        files_to_copy = [
            # 安全库
            "/var/sandbox/nodejs/libseccomp_injector_nodejs.so",
            "/var/sandbox/nodejs/node_runtime"
            # 网络相关文件
            "/etc/ssl/certs/ca-certificates.crt",
            "/etc/nsswitch.conf",
            "/etc/resolv.conf",
            "/etc/hosts",
        ]

        for src_file in files_to_copy:
            if os.path.exists(src_file):
                # 计算目标路径
                # if src_file.startswith("/var/sandbox/nodejs/"):
                #     # 安全库放在沙盒根目录
                #     dst_file = os.path.join(
                #         sandbox_dir, os.path.basename(src_file)
                #     )
                # else:
                # 其他文件保持原路径结构
                rel_path = os.path.relpath(src_file, "/")
                dst_file = os.path.join(sandbox_dir, rel_path)
                dst_dir = os.path.dirname(dst_file)
                os.makedirs(dst_dir, exist_ok=True)

                try:
                    # 使用硬链接而不是复制，减少磁盘I/O
                    if os.path.exists(dst_file):
                        os.remove(dst_file)
                    os.link(src_file, dst_file)

                    if runtime_config.debug_mode:
                        logger.debug(f"链接文件: {src_file} -> {dst_file}")
                except OSError:
                    # 如果硬链接失败，使用复制
                    shutil.copy2(src_file, dst_file)
                    if runtime_config.debug_mode:
                        logger.debug(f"复制文件: {src_file} -> {dst_file}")
            else:
                if runtime_config.debug_mode:
                    logger.debug(f"源文件不存在，跳过: {src_file}")
