"""
Node.js 运行时工具函数
"""

import logging
import os
import shutil
import uuid
from contextlib import contextmanager

logger = logging.getLogger(__name__)


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

            logger.debug(f"创建Node.js沙盒目录: {sandbox_dir}")

            yield sandbox_dir

        finally:
            # 清理沙盒目录
            try:
                if os.path.exists(sandbox_dir):
                    shutil.rmtree(sandbox_dir)
                    logger.debug(f"清理Node.js沙盒目录: {sandbox_dir}")
            except Exception as e:
                logger.debug(f"清理Node.js沙盒目录失败: {e}")

    @staticmethod
    def _copy_nodejs_sandbox_files(sandbox_dir: str):
        """
        复制Node.js沙盒所需的文件和目录

        Args:
            sandbox_dir: 目标沙盒目录
        """
        # 需要复制的文件和目录列表
        items_to_copy = [
            # 安全库
            "/var/sandbox/nodejs/libseccomp_injector_nodejs.so",
            "/var/sandbox/nodejs/runtime",
            # 网络相关文件
            "/etc/ssl/certs/ca-certificates.crt",
            "/etc/nsswitch.conf",
            "/etc/resolv.conf",
            "/etc/hosts",
        ]

        for src_item in items_to_copy:
            if not os.path.exists(src_item):
                logger.debug(f"源路径不存在，跳过: {src_item}")
                continue

            # 计算目标路径
            if src_item.startswith("/var/sandbox/nodejs/"):
                # 安全库放在沙盒根目录
                dst_item = os.path.join(sandbox_dir, os.path.basename(src_item))
            else:
                # 其他文件保持原路径结构
                rel_path = os.path.relpath(src_item, "/")
                dst_item = os.path.join(sandbox_dir, rel_path)

            # 确保目标目录存在
            dst_dir = os.path.dirname(dst_item)
            os.makedirs(dst_dir, exist_ok=True)

            # 添加调试信息
            logger.debug(f"复制项目: {src_item} -> {dst_item}")
            if os.path.isdir(src_item):
                logger.debug(f"源是目录，包含内容: {os.listdir(src_item)[:5]}")

            try:
                if os.path.isdir(src_item):
                    # 复制整个目录
                    if os.path.exists(dst_item):
                        shutil.rmtree(dst_item)
                    shutil.copytree(src_item, dst_item, symlinks=False)
                    logger.debug(f"复制目录: {src_item} -> {dst_item}")
                else:
                    # 复制文件
                    if os.path.exists(dst_item):
                        os.remove(dst_item)
                    # 先尝试硬链接
                    try:
                        os.link(src_item, dst_item)
                        logger.debug(f"链接文件: {src_item} -> {dst_item}")
                    except OSError:
                        # 如果硬链接失败，使用复制
                        shutil.copy2(src_item, dst_item)
                        logger.debug(f"复制文件: {src_item} -> {dst_item}")
            except Exception as e:
                logger.debug(f"复制 {src_item} 失败: {e}")
