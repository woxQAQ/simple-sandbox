import os
import subprocess
import sys

print("Testing system calls...")

# 获取进程信息
print(f"Current PID: {os.getpid()}")
print(f"Current UID: {os.getuid()}")
print(f"Current GID: {os.getgid()}")

# 测试 whoami 命令
try:
    result = subprocess.run(['whoami'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"whoami output: {result.stdout.strip()}")
    else:
        print(f"whoami failed with code {result.returncode}")
except Exception as e:
    print(f"whoami failed: {type(e).__name__}: {e}")

# 测试 ps 命令
try:
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        print(f"ps command executed, found {len(lines)} processes")
    else:
        print(f"ps command failed with code {result.returncode}")
except Exception as e:
    print(f"ps command failed: {type(e).__name__}: {e}")

# 测试基本的文件系统访问
try:
    files = os.listdir('/proc')
    print(f"Successfully listed /proc directory: {len(files)} entries")
except Exception as e:
    print(f"Failed to list /proc: {type(e).__name__}: {e}")

print("System calls test completed")