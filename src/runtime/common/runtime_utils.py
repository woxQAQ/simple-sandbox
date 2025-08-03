"""
运行时公共工具函数
提取Python和Node.js运行时的公共逻辑
"""

import os
import shutil
import traceback
import uuid
from typing import Dict, Optional
from contextlib import contextmanager

from src.config import runtime_config
from src.models import ExecutionResult, ExecutionStatus
from src.runtime.logging_config import create_runtime_logger
from src.utils import (
    create_file_in_dir,
    entrypoint_templates,
    set_executable_permission,
)
from src.utils.crypto_utils import CryptoUtils

logger = create_runtime_logger(__name__)


class RuntimeUtils:
    """运行时公共工具类"""

    @staticmethod
    def encrypt_code(processed_code: str) -> tuple[str, str]:
        """
        加密代码并返回加密后的代码和密钥

        Args:
            processed_code: 预处理后的代码

        Returns:
            tuple: (加密后的代码, 加密密钥)
        """
        crypto_utils = CryptoUtils()
        encryption_key = crypto_utils.generate_encryption_key()
        encrypted_code = crypto_utils.encrypt_code(
            processed_code, encryption_key
        )

        if runtime_config.debug_mode:
            logger.debug("代码加密完成")

        return encrypted_code, encryption_key

    @staticmethod
    def get_seccomp_lib_path(language: str) -> Optional[str]:
        """
        获取seccomp库路径

        Args:
            language: 运行时语言 ('python' 或 'nodejs')

        Returns:
            seccomp库路径，如果不存在则返回None
        """
        if os.path.exists("/var/sandbox"):
            # Docker容器环境路径
            if language == "python":
                lib_path = "/var/sandbox/python/libseccomp_injector_python.so"
            elif language == "nodejs":
                lib_path = "/var/sandbox/nodejs/libseccomp_injector_nodejs.so"
            else:
                return None
        else:
            # 开发环境路径
            base_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "build", "lib"
            )
            if language == "python":
                lib_path = os.path.join(
                    base_path, "libseccomp_injector_python.so"
                )
            elif language == "nodejs":
                lib_path = os.path.join(
                    base_path, "libseccomp_injector_nodejs.so"
                )
            else:
                return None

        # 检查seccomp库是否存在
        if not os.path.exists(lib_path):
            if runtime_config.debug_mode:
                logger.debug(
                    f"seccomp库文件不存在: {lib_path}，跳过seccomp设置"
                )
            return None

        return lib_path

    @staticmethod
    def create_execution_error(
        error_type: str,
        error_message: str,
        execution_time: float,
        exit_code: int = -1,
    ) -> ExecutionResult:
        """
        创建执行错误结果

        Args:
            error_type: 错误类型
            error_message: 错误消息
            execution_time: 执行时间
            exit_code: 退出码

        Returns:
            ExecutionResult: 错误结果对象
        """
        full_error_message = (
            f"{error_type}: {error_message}\\n{traceback.format_exc()}"
        )

        logger.error(
            f"代码执行{error_type} - 错误: {error_message} - 耗时: {execution_time:.3f}s"
        )

        return ExecutionResult(
            status=ExecutionStatus.ERROR,
            stdout="",
            stderr=full_error_message,
            execution_time=execution_time,
            exit_code=exit_code,
            error_message=full_error_message,
        )

    @staticmethod
    def create_timeout_error(execution_time: float) -> ExecutionResult:
        """
        创建超时错误结果

        Args:
            execution_time: 执行时间

        Returns:
            ExecutionResult: 超时结果对象
        """
        logger.warning(f"代码执行超时 - 耗时: {execution_time:.3f}s")

        return ExecutionResult(
            status=ExecutionStatus.TIMEOUT,
            stdout="",
            stderr="Execution timed out",
            execution_time=execution_time,
            exit_code=-1,
            error_message="Execution timed out",
        )

    @staticmethod
    def create_preprocess_error(
        error: Exception, execution_time: float
    ) -> ExecutionResult:
        """
        创建预处理错误结果

        Args:
            error: 预处理异常
            execution_time: 执行时间

        Returns:
            ExecutionResult: 预处理错误结果对象
        """
        return RuntimeUtils.create_execution_error(
            "预处理失败", str(error), execution_time
        )

    @staticmethod
    def create_entrypoint_file(
        sandbox_dir: str,
        language: str,
        encrypted_code: str,
        encryption_key: str,
        seccomp_lib_path: Optional[str],
    ) -> str:
        """
        创建entrypoint文件

        Args:
            sandbox_dir: 沙盒目录
            language: 运行时语言
            encrypted_code: 加密后的代码
            encryption_key: 加密密钥
            seccomp_lib_path: seccomp库路径

        Returns:
            str: entrypoint文件路径
        """
        # 确定文件名
        if language == "python":
            filename = "entrypoint.py"
        elif language == "nodejs":
            filename = "entrypoint.js"
        else:
            raise ValueError(f"不支持的语言: {language}")

        # 创建entrypoint文件
        entrypoint_path = create_file_in_dir(
            sandbox_dir,
            filename,
            entrypoint_templates.create_entrypoint(
                language,
                encrypted_code,
                encryption_key,
                str(runtime_config.sandbox_uid),
                str(runtime_config.sandbox_gid),
                seccomp_lib_path,
            ),
        )

        # 设置执行权限
        set_executable_permission(entrypoint_path)

        if runtime_config.debug_mode:
            logger.debug(f"创建{language} entrypoint文件: {entrypoint_path}")

        return entrypoint_path

    @staticmethod
    def create_python_entrypoint_file(
        encrypted_code: str,
        encryption_key: str,
        seccomp_lib_path: Optional[str],
        sandbox_dir: str = "/var/sandbox/python",
    ) -> str:
        """
        创建Python专用的entrypoint文件，使用固定的/var/sandbox/python/tmp目录

        Args:
            encrypted_code: 加密后的代码
            encryption_key: 加密密钥
            seccomp_lib_path: seccomp库路径

        Returns:
            str: entrypoint文件路径
        """
        # 创建/tmp目录（如果不存在）
        tmp_dir = os.path.join(sandbox_dir, "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        
        # 生成UUID文件名
        filename = f"entrypoint-{uuid.uuid4()}.py"
        entrypoint_path = os.path.join(tmp_dir, filename)
        
        # 创建entrypoint文件
        with open(entrypoint_path, 'w') as f:
            f.write(entrypoint_templates.create_entrypoint(
                "python",
                encrypted_code,
                encryption_key,
                str(runtime_config.sandbox_uid),
                str(runtime_config.sandbox_gid),
                seccomp_lib_path,
            ))
        
        # 设置执行权限
        set_executable_permission(entrypoint_path)
        
        if runtime_config.debug_mode:
            logger.debug(f"创建Python entrypoint文件: {entrypoint_path}")
        
        return entrypoint_path

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
            RuntimeUtils._copy_nodejs_sandbox_files(sandbox_dir)
            
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
            # 网络相关文件
            "/etc/ssl/certs/ca-certificates.crt",
            "/etc/nsswitch.conf",
            "/etc/resolv.conf",
            "/etc/hosts",
        ]
        
        for src_file in files_to_copy:
            if os.path.exists(src_file):
                # 计算目标路径
                if src_file.startswith("/var/sandbox/nodejs/"):
                    # 安全库放在沙盒根目录
                    dst_file = os.path.join(sandbox_dir, os.path.basename(src_file))
                else:
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

    @staticmethod
    def setup_process_environment() -> Dict[str, str]:
        """
        设置进程环境变量

        Returns:
            Dict[str, str]: 环境变量字典
        """
        return {"PATH": os.environ.get("PATH", "")}

    @staticmethod
    def log_execution_result(
        language: str, result: ExecutionResult, execution_time: float
    ) -> None:
        """
        记录执行结果日志

        Args:
            language: 运行时语言
            result: 执行结果
            execution_time: 执行时间
        """
        if result.status == ExecutionStatus.SUCCESS:
            logger.info(
                f"{language}代码执行成功 - 状态: {result.exit_code} - "
                f"执行时间: {execution_time:.3f}s - "
                f"stdout长度: {len(result.stdout)} - stderr长度: {len(result.stderr)}"
            )
        else:
            logger.warning(
                f"{language}代码执行失败 - 状态: {result.exit_code} - "
                f"执行时间: {execution_time:.3f}s - "
                f"stdout长度: {len(result.stdout)} - stderr长度: {len(result.stderr)} - "
                f"stderr: {result.stderr[:200]}{'...' if len(result.stderr) > 200 else ''}"
            )
