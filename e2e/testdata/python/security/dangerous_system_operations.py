import os
import subprocess
import sys

# 测试各种危险操作
dangerous_operations = [
    # 尝试更改权限
    ('chmod', ['chmod', '777', '/tmp']),
    # 尝试挂载文件系统
    ('mount', ['mount', '/dev/null', '/tmp']),
    # 尝试创建设备文件
    ('mknod', ['mknod', '/tmp/testdev', 'c', '1', '1']),
    # 尝试修改系统时间
    ('date', ['date', '-s', '2023-01-01']),
    # 尝试加载内核模块
    ('modprobe', ['modprobe', 'dummy']),
]

for name, cmd in dangerous_operations:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            print(f"WARNING: {name} succeeded")
        else:
            print(f"GOOD: {name} failed with code {result.returncode}")
    except subprocess.TimeoutExpired:
        print(f"GOOD: {name} timed out")
    except FileNotFoundError:
        print(f"GOOD: {name} command not found")
    except Exception as e:
        print(f"GOOD: {name} blocked: {type(e).__name__}")

# 测试直接系统调用
try:
    os.setuid(0)  # 尝试切换到 root
    print("WARNING: setuid(0) succeeded")
except PermissionError:
    print("GOOD: setuid(0) blocked")
except Exception as e:
    print(f"GOOD: setuid(0) failed: {type(e).__name__}")