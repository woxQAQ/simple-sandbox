import os

# 测试访问危险的系统目录
dangerous_directories = [
    '/root',
    '/home',
    '/var/log',
    '/boot',
    '/usr/local/bin'
]

# 测试访问容器内正常的系统目录
normal_directories = [
    '/etc',
    '/proc',
    '/sys',
    '/dev',
    '/tmp'
]

print("Testing dangerous directories:")
for directory in dangerous_directories:
    try:
        files = os.listdir(directory)
        print(f"WARNING: Can access dangerous {directory}: {len(files)} files")
    except (PermissionError, FileNotFoundError) as e:
        print(f"GOOD: {directory} properly restricted")
    except Exception as e:
        print(f"GOOD: Cannot access {directory}: {type(e).__name__}")

print("\nTesting normal container directories:")
for directory in normal_directories:
    try:
        files = os.listdir(directory)
        print(f"INFO: Can access container {directory}: {len(files)} files")
    except Exception as e:
        print(f"INFO: Cannot access {directory}: {type(e).__name__}")