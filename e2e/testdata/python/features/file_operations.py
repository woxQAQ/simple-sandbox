import os
import tempfile

print("Testing file operations...")

# 测试读取 /etc/passwd（容器内正常操作）
try:
    with open('/etc/passwd', 'r') as f:
        content = f.read()
        print(f"Successfully read /etc/passwd ({len(content)} characters)")
except Exception as e:
    print(f"Failed to read /etc/passwd: {e}")

# 测试写入临时文件
try:
    with open('/tmp/test.txt', 'w') as f:
        f.write("Hello from sandbox!\n")
    print("Successfully wrote to /tmp/test.txt")
except Exception as e:
    print(f"Failed to write to /tmp/test.txt: {e}")

# 测试读取刚写入的文件
try:
    with open('/tmp/test.txt', 'r') as f:
        content = f.read()
        print(f"Successfully read from /tmp/test.txt: {content.strip()}")
except Exception as e:
    print(f"Failed to read from /tmp/test.txt: {e}")

# 测试列出目录内容
try:
    files = os.listdir('/tmp')
    print(f"Found {len(files)} files in /tmp")
except Exception as e:
    print(f"Failed to list /tmp: {e}")

print("File operations test completed")