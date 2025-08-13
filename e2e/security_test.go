package e2e_test

import (
	"strings"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/woxqaq/simple-sandbox/e2e/testdata"
	"github.com/woxqaq/simple-sandbox/e2e/utils"
	"github.com/woxqaq/simple-sandbox/internal/models"
)

var _ = Describe("Security Tests", func() {
	var (
		testServer *utils.TestServer
		httpClient *utils.HTTPClient
	)

	BeforeEach(func() {
		testServer = utils.NewTestServer("8083")
		err := testServer.Start()
		Expect(err).NotTo(HaveOccurred())
		httpClient = utils.NewHTTPClient(testServer.GetBaseURL())
	})

	AfterEach(func() {
		if testServer != nil {
			testServer.Stop()
		}
	})

	Describe("File System Isolation", func() {
		Context("Python runtime", func() {
			It("should prevent access to sensitive system files", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["file_operations"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))

				// 应该无法读取 /etc/passwd
				Expect(result.Stdout).To(ContainSubstring("Failed to read /etc/passwd"))
				// 但应该能够写入 /tmp
				Expect(result.Stdout).To(ContainSubstring("Successfully wrote to /tmp/test.txt"))
			})

			It("should prevent access to host filesystem", func() {
				code := `
import os

# 尝试访问各种系统目录
directories_to_test = [
    '/etc',
    '/proc',
    '/sys',
    '/dev',
    '/root',
    '/home',
    '/var/log'
]

for directory in directories_to_test:
    try:
        files = os.listdir(directory)
        print(f"WARNING: Can access {directory}: {len(files)} files")
    except PermissionError:
        print(f"GOOD: Permission denied for {directory}")
    except FileNotFoundError:
        print(f"GOOD: Directory {directory} not found")
    except Exception as e:
        print(f"GOOD: Cannot access {directory}: {e}")
`
				req := &models.RunRequest{
					Language:    "python",
					Code:        code,
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))

				// 大部分目录应该无法访问
				Expect(result.Stdout).To(ContainSubstring("GOOD:"))
				// 不应该有太多 WARNING
				warningCount := strings.Count(result.Stdout, "WARNING:")
				Expect(warningCount).To(BeNumerically("<", 3), "Too many directories are accessible")
			})
		})

		Context("Node.js runtime", func() {
			It("should prevent access to sensitive system files", func() {
				req := &models.RunRequest{
					Language:    "node",
					Code:        testdata.NodeCodes["file_operations"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))

				// 应该无法读取 /etc/passwd
				Expect(result.Stdout).To(ContainSubstring("Failed to read /etc/passwd"))
				// 但应该能够写入 /tmp
				Expect(result.Stdout).To(ContainSubstring("Successfully wrote to /tmp/test.txt"))
			})
		})
	})

	Describe("Network Isolation", func() {
		Context("Python runtime", func() {
			It("should prevent external network access", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["network_test"],
					TimeLimitMs: 10000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))

				// 网络访问应该失败
				Expect(result.Stdout).To(ContainSubstring("Network access failed"))
			})

			It("should block various network protocols", func() {
				code := `
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
`
				req := &models.RunRequest{
					Language:    "python",
					Code:        code,
					TimeLimitMs: 10000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))

				// 大部分网络访问应该被阻止
				Expect(result.Stdout).To(ContainSubstring("GOOD:"))
				warningCount := strings.Count(result.Stdout, "WARNING:")
				Expect(warningCount).To(BeNumerically("<", 2), "Too many network accesses are allowed")
			})
		})

		Context("Node.js runtime", func() {
			It("should prevent external network access", func() {
				req := &models.RunRequest{
					Language:    "node",
					Code:        testdata.NodeCodes["network_test"],
					TimeLimitMs: 10000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))

				// 网络访问应该失败
				Expect(result.Stdout).To(Or(
					ContainSubstring("Network access failed"),
					ContainSubstring("Request timeout"),
				))
			})
		})
	})

	Describe("System Call Restrictions", func() {
		Context("Python runtime", func() {
			It("should allow basic system calls but restrict dangerous ones", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["system_calls"],
					TimeLimitMs: 10000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))

				// 应该能够获取基本的进程信息
				Expect(result.Stdout).To(ContainSubstring("Current PID:"))
				Expect(result.Stdout).To(ContainSubstring("Current UID:"))
				Expect(result.Stdout).To(ContainSubstring("Current GID:"))

				// whoami 应该显示 sandbox 用户
				Expect(result.Stdout).To(ContainSubstring("whoami output: sandbox"))
			})

			It("should prevent dangerous system operations", func() {
				code := `
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
`
				req := &models.RunRequest{
					Language:    "python",
					Code:        code,
					TimeLimitMs: 10000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))

				// 大部分危险操作应该被阻止
				Expect(result.Stdout).To(ContainSubstring("GOOD:"))
				warningCount := strings.Count(result.Stdout, "WARNING:")
				Expect(warningCount).To(BeNumerically("<", 2), "Too many dangerous operations are allowed")
			})
		})

		Context("Node.js runtime", func() {
			It("should allow basic system calls but restrict dangerous ones", func() {
				req := &models.RunRequest{
					Language:    "node",
					Code:        testdata.NodeCodes["system_calls"],
					TimeLimitMs: 10000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))

				// 应该能够获取基本的进程信息
				Expect(result.Stdout).To(ContainSubstring("Current PID:"))
				Expect(result.Stdout).To(ContainSubstring("Current UID:"))
				Expect(result.Stdout).To(ContainSubstring("Current GID:"))

				// whoami 应该显示 sandbox 用户
				Expect(result.Stdout).To(ContainSubstring("whoami output: sandbox"))
			})
		})
	})

	Describe("User and Permission Isolation", func() {
		It("should run as non-root user in Python", func() {
			code := `
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
`
			req := &models.RunRequest{
				Language:    "python",
				Code:        code,
				TimeLimitMs: 5000,
				MemoryMB:    128,
			}

			result, err := httpClient.RunCode(req)
			Expect(err).NotTo(HaveOccurred())
			Expect(result.ExitCode).To(Equal(0))

			// 应该以非 root 用户运行
			Expect(result.Stdout).To(ContainSubstring("GOOD: Running as non-root user"))
			Expect(result.Stdout).To(ContainSubstring("Username: sandbox"))
			Expect(result.Stdout).NotTo(ContainSubstring("WARNING: Running as root!"))
		})

		It("should run as non-root user in Node.js", func() {
			code := `
const os = require('os');

const uid = process.getuid();
const gid = process.getgid();

console.log('Running as UID: ' + uid);
console.log('Running as GID: ' + gid);
console.log('Username: ' + os.userInfo().username);
console.log('Home directory: ' + os.userInfo().homedir);

// 检查是否为 root
if (uid === 0) {
    console.log('WARNING: Running as root!');
} else {
    console.log('GOOD: Running as non-root user');
}
`
			req := &models.RunRequest{
				Language:    "node",
				Code:        code,
				TimeLimitMs: 5000,
				MemoryMB:    128,
			}

			result, err := httpClient.RunCode(req)
			Expect(err).NotTo(HaveOccurred())
			Expect(result.ExitCode).To(Equal(0))

			// 应该以非 root 用户运行
			Expect(result.Stdout).To(ContainSubstring("GOOD: Running as non-root user"))
			Expect(result.Stdout).To(ContainSubstring("Username: sandbox"))
			Expect(result.Stdout).NotTo(ContainSubstring("WARNING: Running as root!"))
		})
	})

	Describe("Resource Limits", func() {
		It("should enforce memory limits", func() {
			req := &models.RunRequest{
				Language:    "python",
				Code:        testdata.PythonCodes["memory_intensive"],
				TimeLimitMs: 10000,
				MemoryMB:    32, // 非常小的内存限制
			}

			result, err := httpClient.RunCode(req)
			Expect(err).NotTo(HaveOccurred())

			// 内存限制应该生效，进程可能被终止或出现内存错误
			if result.ExitCode != 0 {
				// 检查是否是内存相关的错误
				Expect(result.Stderr).To(Or(
					ContainSubstring("MemoryError"),
					ContainSubstring("killed"),
					ContainSubstring("OOM"),
					ContainSubstring("memory"),
				))
			}
		})

		It("should enforce time limits", func() {
			req := &models.RunRequest{
				Language:    "python",
				Code:        testdata.PythonCodes["infinite_loop"],
				TimeLimitMs: 2000, // 2 秒超时
				MemoryMB:    128,
			}

			result, err := httpClient.RunCode(req)
			Expect(err).NotTo(HaveOccurred())

			// 时间限制应该生效，进程应该被终止
			Expect(result.ExitCode).NotTo(Equal(0))
			Expect(result.DurationMs).To(BeNumerically(">=", 2000))
			Expect(result.DurationMs).To(BeNumerically("<", 5000))
		})
	})

	Describe("Container Security", func() {
		It("should prevent container escape attempts", func() {
			code := `
import os
import subprocess

# 尝试各种容器逃逸技术
escape_attempts = [
    # 尝试访问 Docker socket
    ('docker_socket', ['ls', '-la', '/var/run/docker.sock']),
    # 尝试访问 proc 文件系统中的敏感信息
    ('proc_mounts', ['cat', '/proc/mounts']),
    # 尝试访问 cgroup 信息
    ('cgroup', ['cat', '/proc/1/cgroup']),
    # 尝试访问内核信息
    ('kernel_version', ['uname', '-a']),
]

for name, cmd in escape_attempts:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        if result.returncode == 0 and result.stdout.strip():
            print(f"INFO: {name} accessible: {len(result.stdout)} chars")
        else:
            print(f"GOOD: {name} not accessible")
    except Exception as e:
        print(f"GOOD: {name} blocked: {type(e).__name__}")

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
`
			req := &models.RunRequest{
				Language:    "python",
				Code:        code,
				TimeLimitMs: 10000,
				MemoryMB:    128,
			}

			result, err := httpClient.RunCode(req)
			Expect(err).NotTo(HaveOccurred())
			Expect(result.ExitCode).To(Equal(0))

			// 应该在容器中运行
			Expect(result.Stdout).To(ContainSubstring("INFO: Running in container (expected)"))
			// Docker socket 应该不可访问
			Expect(result.Stdout).To(ContainSubstring("docker_socket not accessible"))
		})
	})
})
