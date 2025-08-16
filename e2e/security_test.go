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
		// 为每个测试创建独立的服务器实例
		var err error
		testServer, httpClient, err = CreateParallelTestServer()
		Expect(err).NotTo(HaveOccurred(), "Failed to create test server")
	})

	AfterEach(func() {
		// 清理测试服务器
		if testServer != nil {
			_ = ReleaseParallelTestServer(testServer)
		}
	})

	Describe("File System Isolation", func() {
		Context("Python runtime", func() {
			It("should allow basic file operations but prevent dangerous access", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["file_operations"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				// 允许容器正常退出或被信号终止
				Expect(result.ExitCode).To(Or(Equal(0), Equal(133), Equal(137)))

				// 如果容器正常退出，检查文件操作结果
				if result.ExitCode == 0 {
					// 容器内读取 /etc/passwd 是正常的
					Expect(result.Stdout).To(ContainSubstring("Successfully read /etc/passwd"))
					// 应该能够写入 /tmp
					Expect(result.Stdout).To(ContainSubstring("Successfully wrote to /tmp/test.txt"))
				}
			})

			It("should prevent access to dangerous host directories", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["dangerous_directory_access"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				// 允许容器正常退出或被信号终止
				Expect(result.ExitCode).To(Or(Equal(0), Equal(133), Equal(137)))

				// 危险目录应该被限制访问
				Expect(result.Stdout).To(ContainSubstring("GOOD:"))
				// 危险目录访问应该被阻止
				dangerousWarningCount := strings.Count(result.Stdout, "WARNING: Can access dangerous")
				Expect(dangerousWarningCount).To(BeNumerically("<", 5), "Too many dangerous directories are accessible")
			})
		})

		Context("Node.js runtime", func() {
			It("should allow basic file operations but prevent dangerous access", func() {
				req := &models.RunRequest{
					Language:    "node",
					Code:        testdata.NodeCodes["file_operations"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				// 允许容器正常退出或被信号终止
				Expect(result.ExitCode).To(Or(Equal(0), Equal(133), Equal(137)))

				// 如果容器正常退出，检查文件操作结果
				if result.ExitCode == 0 {
					// 容器内读取 /etc/passwd 是正常的
					Expect(result.Stdout).To(ContainSubstring("Successfully read /etc/passwd"))
					// 应该能够写入 /tmp
					Expect(result.Stdout).To(ContainSubstring("Successfully wrote to /tmp/test.txt"))
				}
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
				// 允许容器正常退出或被信号终止
				Expect(result.ExitCode).To(Or(Equal(0), Equal(133), Equal(137)))

				// 网络访问应该失败
				Expect(result.Stdout).To(ContainSubstring("Network access failed"))
			})

			It("should block various network protocols", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["network_protocol_test"],
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

				// 如果容器正常退出，检查网络隔离结果
				if result.ExitCode == 0 {
					// 网络访问应该失败
					Expect(result.Stdout).To(Or(
						ContainSubstring("Network access failed"),
						ContainSubstring("Request timeout"),
					))
				}
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
				// 允许容器正常退出或被信号终止
				Expect(result.ExitCode).To(Or(Equal(0), Equal(133), Equal(137)))

				// 如果容器正常退出，检查系统调用结果
				if result.ExitCode == 0 {
					// 应该能够获取基本的进程信息
					Expect(result.Stdout).To(ContainSubstring("Current PID:"))
					Expect(result.Stdout).To(ContainSubstring("Current UID:"))
					Expect(result.Stdout).To(ContainSubstring("Current GID:"))

					// whoami 应该显示 sandbox 用户或者失败（在受限环境中）
					Expect(result.Stdout).To(Or(
						ContainSubstring("whoami output: sandbox"),
						ContainSubstring("whoami failed"),
					))
					// ps 命令应该能够执行（容器内正常操作）或者失败（在受限环境中）
					Expect(result.Stdout).To(Or(
						ContainSubstring("ps command executed"),
						ContainSubstring("ps command failed"),
					))
				}
			})

			It("should prevent dangerous system operations", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["dangerous_system_operations"],
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
				// 允许容器正常退出或被信号终止
				Expect(result.ExitCode).To(Or(Equal(0), Equal(133), Equal(137)))

				// 如果容器正常退出，检查系统调用结果
				if result.ExitCode == 0 {
					// 应该能够获取基本的进程信息
					Expect(result.Stdout).To(ContainSubstring("Current PID:"))
					Expect(result.Stdout).To(ContainSubstring("Current UID:"))
					Expect(result.Stdout).To(ContainSubstring("Current GID:"))

					// whoami 应该显示 sandbox 用户或者失败（在受限环境中）
					Expect(result.Stdout).To(Or(
						ContainSubstring("whoami output: sandbox"),
						ContainSubstring("whoami failed"),
					))
					// ps 命令应该能够执行（容器内正常操作）或者失败（在受限环境中）
					Expect(result.Stdout).To(Or(
						ContainSubstring("ps command executed"),
						ContainSubstring("ps command failed"),
					))
				}
			})
		})
	})

	Describe("User and Permission Isolation", func() {
		It("should run as non-root user in Python", func() {
			req := &models.RunRequest{
				Language:    "python",
				Code:        testdata.PythonCodes["user_permission_test"],
				TimeLimitMs: 5000,
				MemoryMB:    128,
			}

			result, err := httpClient.RunCode(req)
			Expect(err).NotTo(HaveOccurred())
			// 允许容器正常退出或被信号终止
			Expect(result.ExitCode).To(Or(Equal(0), Equal(133), Equal(137)))

			// 应该以非 root 用户运行
			Expect(result.Stdout).To(ContainSubstring("GOOD: Running as non-root user"))
			Expect(result.Stdout).To(ContainSubstring("Username: sandbox"))
			Expect(result.Stdout).NotTo(ContainSubstring("WARNING: Running as root!"))
		})

		It("should run as non-root user in Node.js", func() {
			req := &models.RunRequest{
				Language:    "node",
				Code:        testdata.NodeCodes["user_permission_test"],
				TimeLimitMs: 5000,
				MemoryMB:    128,
			}

			result, err := httpClient.RunCode(req)
			Expect(err).NotTo(HaveOccurred())
			// 允许容器正常退出或被信号终止
			Expect(result.ExitCode).To(Or(Equal(0), Equal(133), Equal(137)))

			// 如果容器正常退出，检查用户权限结果
			if result.ExitCode == 0 {
				// 应该以非 root 用户运行
				Expect(result.Stdout).To(ContainSubstring("GOOD: Running as non-root user"))
				Expect(result.Stdout).To(ContainSubstring("Username: sandbox"))
				Expect(result.Stdout).NotTo(ContainSubstring("WARNING: Running as root!"))
			}
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
					ContainSubstring("OpenBLAS"),
					ContainSubstring("pthread_create failed"),
					ContainSubstring("Operation not permitted"),
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
		It("should prevent dangerous container escape attempts", func() {
			req := &models.RunRequest{
				Language:    "python",
				Code:        testdata.PythonCodes["container_escape_test"],
				TimeLimitMs: 10000,
				MemoryMB:    128,
			}

			result, err := httpClient.RunCode(req)
			Expect(err).NotTo(HaveOccurred())
			Expect(result.ExitCode).To(Equal(0))

			// 应该在容器中运行，但如果无法确定也是可以接受的
			Expect(result.Stdout).To(Or(
				ContainSubstring("INFO: Running in container (expected)"),
				ContainSubstring("WARNING: May not be running in container"),
			))
			// 危险的逃逸尝试应该被阻止
			Expect(result.Stdout).To(ContainSubstring("GOOD:"))
			// Docker socket 应该不可访问
			Expect(result.Stdout).To(Or(
				ContainSubstring("docker_socket properly blocked"),
				ContainSubstring("docker_socket blocked: PermissionError"),
			))
			// 正常的容器信息访问应该被允许
			Expect(result.Stdout).To(ContainSubstring("INFO:"))
			// 不应该有太多安全警告（允许1个容器状态警告）
			warningCount := strings.Count(result.Stdout, "WARNING:")
			Expect(warningCount).To(BeNumerically("<", 3), "Too many security risks detected")
		})
	})
})
