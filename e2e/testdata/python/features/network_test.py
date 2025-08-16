import socket
import urllib.request
import sys

print("Testing network access...")

# 测试HTTP访问
try:
    response = urllib.request.urlopen('http://httpbin.org/get', timeout=3)
    print("HTTP access succeeded - this should be blocked")
except Exception as e:
    print(f"Network access failed: {type(e).__name__}: {e}")

# 测试DNS解析
try:
    socket.gethostbyname('google.com')
    print("DNS resolution succeeded - this should be blocked")
except Exception as e:
    print(f"DNS resolution failed: {type(e).__name__}: {e}")

# 测试原始套接字连接
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    sock.connect(('8.8.8.8', 53))
    print("Raw socket connection succeeded - this should be blocked")
    sock.close()
except Exception as e:
    print(f"Raw socket connection failed: {type(e).__name__}: {e}")

print("Network test completed - network access should be blocked in sandbox")