#!/usr/bin/env python3
"""
安全执行示例
演示如何使用新的seccomp安全功能来执行不受信任的代码
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.runtime.manager import ProcessManager
from src.security import SecurityManager, SecurityError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demonstrate_security_features():
    """演示安全功能"""
    logger.info("=== Seccomp Security Features Demonstration ===")
    
    # 1. 检查平台支持
    security_manager = SecurityManager()
    logger.info(f"Platform: {os.uname().sysname}")
    logger.info(f"Architecture: {os.uname().machine}")
    logger.info(f"Seccomp supported: {security_manager.is_seccomp_supported()}")
    
    # 2. 显示支持的语言
    supported_languages = security_manager.get_supported_languages()
    logger.info(f"Supported languages: {supported_languages}")
    
    # 3. 显示各语言的系统调用数量
    for language in supported_languages:
        syscalls = security_manager.get_syscalls_for_language(language)
        logger.info(f"{language}: {len(syscalls)} allowed syscalls")
    
    return security_manager.is_seccomp_supported()


def run_secure_python_code():
    """运行安全的Python代码示例"""
    logger.info("\n=== Secure Python Code Execution ===")
    
    # 创建进程管理器（启用seccomp）
    process_manager = ProcessManager(enable_seccomp=True)
    
    # 要执行的Python代码
    python_code = """
print("Hello from secure sandbox!")
print(f"Current working directory: {os.getcwd()}")
print(f"Process ID: {os.getpid()}")

# 尝试一些基本操作
import sys
print(f"Python version: {sys.version}")

# 计算示例
result = sum(range(100))
print(f"Sum of 0-99: {result}")

print("Secure execution completed successfully!")
"""
    
    # 执行代码
    try:
        result = process_manager.execute_process(
            command=["python3", "-c", python_code],
            timeout=10,
            memory_limit=128,  # 128MB
            language="python",
            sandbox_uid=65534,  # nobody用户
            sandbox_gid=65534,  # nobody组
        )
        
        logger.info(f"Execution status: {result.status}")
        logger.info(f"Exit code: {result.exit_code}")
        logger.info(f"Execution time: {result.execution_time:.3f}s")
        
        if result.stdout:
            logger.info("STDOUT:")
            for line in result.stdout.strip().split('\n'):
                logger.info(f"  {line}")
        
        if result.stderr:
            logger.info("STDERR:")
            for line in result.stderr.strip().split('\n'):
                logger.info(f"  {line}")
                
    except Exception as e:
        logger.error(f"Failed to execute secure code: {e}")


def run_restricted_code_example():
    """运行受限代码示例（演示seccomp限制）"""
    logger.info("\n=== Restricted Code Example ===")
    
    process_manager = ProcessManager(enable_seccomp=True)
    
    # 尝试执行可能被seccomp阻止的操作
    restricted_code = """
import os
import subprocess

print("Attempting restricted operations...")

try:
    # 尝试创建子进程（可能被限制）
    result = subprocess.run(['echo', 'test'], capture_output=True, text=True)
    print(f"Subprocess result: {result.stdout.strip()}")
except Exception as e:
    print(f"Subprocess failed: {e}")

try:
    # 尝试网络操作（可能被限制）
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket created successfully")
    sock.close()
except Exception as e:
    print(f"Socket operation failed: {e}")

print("Restricted code execution completed")
"""
    
    try:
        result = process_manager.execute_process(
            command=["python3", "-c", restricted_code],
            timeout=10,
            memory_limit=128,
            language="python",
            sandbox_uid=65534,
            sandbox_gid=65534,
        )
        
        logger.info(f"Restricted execution status: {result.status}")
        logger.info(f"Exit code: {result.exit_code}")
        
        if result.stdout:
            logger.info("STDOUT:")
            for line in result.stdout.strip().split('\n'):
                logger.info(f"  {line}")
        
        if result.stderr:
            logger.info("STDERR:")
            for line in result.stderr.strip().split('\n'):
                logger.info(f"  {line}")
                
    except Exception as e:
        logger.error(f"Failed to execute restricted code: {e}")


def compare_with_without_seccomp():
    """比较启用和禁用seccomp的执行"""
    logger.info("\n=== Comparison: With vs Without Seccomp ===")
    
    test_code = """
import os
print(f"PID: {os.getpid()}")
print(f"UID: {os.getuid()}")
print(f"GID: {os.getgid()}")
print("Basic execution test")
"""
    
    # 不启用seccomp
    logger.info("--- Without Seccomp ---")
    process_manager_no_seccomp = ProcessManager(enable_seccomp=False)
    
    try:
        result = process_manager_no_seccomp.execute_process(
            command=["python3", "-c", test_code],
            timeout=5,
            memory_limit=64,
            language="python",
        )
        logger.info(f"Status: {result.status}, Time: {result.execution_time:.3f}s")
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                logger.info(f"  {line}")
    except Exception as e:
        logger.error(f"No-seccomp execution failed: {e}")
    
    # 启用seccomp
    logger.info("--- With Seccomp ---")
    process_manager_seccomp = ProcessManager(enable_seccomp=True)
    
    try:
        result = process_manager_seccomp.execute_process(
            command=["python3", "-c", test_code],
            timeout=5,
            memory_limit=64,
            language="python",
            sandbox_uid=65534,
            sandbox_gid=65534,
        )
        logger.info(f"Status: {result.status}, Time: {result.execution_time:.3f}s")
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                logger.info(f"  {line}")
    except Exception as e:
        logger.error(f"Seccomp execution failed: {e}")


def main():
    """主函数"""
    logger.info("Starting secure execution demonstration...")
    
    try:
        # 演示安全功能
        seccomp_supported = demonstrate_security_features()
        
        if seccomp_supported:
            # 运行安全代码示例
            run_secure_python_code()
            
            # 运行受限代码示例
            run_restricted_code_example()
            
            # 比较启用/禁用seccomp
            compare_with_without_seccomp()
        else:
            logger.warning("Seccomp not supported on this platform")
            logger.info("Running basic execution test without seccomp...")
            
            # 在不支持seccomp的平台上运行基本测试
            process_manager = ProcessManager(enable_seccomp=False)
            result = process_manager.execute_process(
                command=["python3", "-c", "print('Hello from basic sandbox!')"],
                timeout=5,
                memory_limit=64,
            )
            logger.info(f"Basic test result: {result.status}")
            if result.stdout:
                logger.info(f"Output: {result.stdout.strip()}")
        
        logger.info("\n=== Demonstration completed ===")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()