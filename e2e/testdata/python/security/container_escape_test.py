import os
import subprocess

# 测试真正危险的容器逃逸尝试
dangerous_attempts = [
    # 尝试访问 Docker socket（真正危险）
    ('docker_socket', ['ls', '-la', '/var/run/docker.sock']),
    # 尝试挂载文件系统（危险）
    ('mount_attempt', ['mount', '/dev/null', '/tmp/test']),
    # 尝试访问主机网络命名空间（危险）
    ('host_network', ['ip', 'netns', 'list']),
]

# 测试容器内正常的系统信息访问
normal_info_access = [
    # 容器内访问 proc 文件系统是正常的
    ('proc_mounts', ['cat', '/proc/mounts']),
    # 访问 cgroup 信息是正常的
    ('cgroup', ['cat', '/proc/1/cgroup']),
    # 访问内核信息是正常的
    ('kernel_version', ['uname', '-a']),
]

print("Testing dangerous escape attempts:")
for name, cmd in dangerous_attempts:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        if result.returncode == 0 and result.stdout.strip():
            print(f"WARNING: {name} accessible - potential security risk")
        else:
            print(f"GOOD: {name} properly blocked")
    except Exception as e:
        print(f"GOOD: {name} blocked: {type(e).__name__}")

print("\nTesting normal container info access:")
for name, cmd in normal_info_access:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        if result.returncode == 0 and result.stdout.strip():
            print(f"INFO: {name} accessible (normal): {len(result.stdout)} chars")
        else:
            print(f"INFO: {name} not accessible")
    except Exception as e:
        print(f"INFO: {name} access failed: {type(e).__name__}")

# 检查是否在容器中
try:
    with open('/proc/1/cgroup', 'r') as f:
        cgroup_content = f.read()
        if 'docker' in cgroup_content or 'containerd' in cgroup_content:
            print("INFO: Running in container (expected)")
        else:
            print("WARNING: May not be running in container")
except Exception as e:
    print(f"Cannot determine container status: {e}")