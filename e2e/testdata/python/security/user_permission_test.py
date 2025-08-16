import os
import pwd

uid = os.getuid()
gid = os.getgid()

print(f"Running as UID: {uid}")
print(f"Running as GID: {gid}")

try:
    user_info = pwd.getpwuid(uid)
    print(f"Username: {user_info.pw_name}")
    print(f"Home directory: {user_info.pw_dir}")
    print(f"Shell: {user_info.pw_shell}")
except Exception as e:
    print(f"Could not get user info: {e}")

# 检查是否为 root
if uid == 0:
    print("WARNING: Running as root!")
else:
    print("GOOD: Running as non-root user")