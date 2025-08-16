import socket
import urllib.request

# 测试不同的网络协议和端口
test_cases = [
    ('HTTP', 'http://httpbin.org/get'),
    ('HTTPS', 'https://httpbin.org/get'),
    ('DNS', 'google.com'),
]

for protocol, target in test_cases:
    try:
        if protocol in ['HTTP', 'HTTPS']:
            response = urllib.request.urlopen(target, timeout=3)
            print(f"WARNING: {protocol} access to {target} succeeded")
        elif protocol == 'DNS':
            socket.gethostbyname(target)
            print(f"WARNING: DNS resolution for {target} succeeded")
    except Exception as e:
        print(f"GOOD: {protocol} access blocked: {type(e).__name__}")

# 测试原始套接字
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    sock.connect(('8.8.8.8', 53))
    print("WARNING: Raw socket connection succeeded")
    sock.close()
except Exception as e:
    print(f"GOOD: Raw socket blocked: {type(e).__name__}")