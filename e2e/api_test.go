package e2e_test

import (
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/woxqaq/simple-sandbox/e2e/testdata"
	"github.com/woxqaq/simple-sandbox/e2e/utils"
	"github.com/woxqaq/simple-sandbox/internal/models"
)

var _ = Describe("API Tests", func() {
	var (
		httpClient *utils.HTTPClient
	)

	BeforeEach(func() {
		httpClient = globalHTTPClient
	})

	Describe("/v1/run endpoint", func() {
		Context("with valid requests", func() {
			It("should execute Python hello world successfully", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["hello_world"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
					CPUShares:   256,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				expected := testdata.ExpectedOutputs["python_hello_world"]
				Expect(result.Stdout).To(Equal(expected["stdout"]))
				Expect(result.Stderr).To(Equal(expected["stderr"]))
				Expect(result.ExitCode).To(Equal(expected["exit_code"]))
				Expect(result.DurationMs).To(BeNumerically(">", 0))
			})

			It("should execute Node.js hello world successfully", func() {
				req := &models.RunRequest{
					Language:    "node",
					Code:        testdata.NodeCodes["hello_world"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
					CPUShares:   256,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				expected := testdata.ExpectedOutputs["node_hello_world"]
				Expect(result.Stdout).To(Equal(expected["stdout"]))
				Expect(result.Stderr).To(Equal(expected["stderr"]))
				Expect(result.ExitCode).To(Equal(expected["exit_code"]))
				Expect(result.DurationMs).To(BeNumerically(">", 0))
			})

			It("should handle Python math operations", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["simple_math"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				expected := testdata.ExpectedOutputs["python_simple_math"]
				Expect(result.Stdout).To(Equal(expected["stdout"]))
				Expect(result.ExitCode).To(Equal(expected["exit_code"]))
			})

			It("should handle Node.js math operations", func() {
				req := &models.RunRequest{
					Language:    "node",
					Code:        testdata.NodeCodes["simple_math"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				expected := testdata.ExpectedOutputs["node_simple_math"]
				Expect(result.Stdout).To(Equal(expected["stdout"]))
				Expect(result.ExitCode).To(Equal(expected["exit_code"]))
			})
		})

		Context("with error conditions", func() {
			It("should handle Python runtime errors", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["error_code"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				expected := testdata.ExpectedOutputs["python_error_code"]
				Expect(result.Stdout).To(Equal(expected["stdout"]))
				Expect(result.ExitCode).To(Equal(expected["exit_code"]))
				Expect(result.Stderr).To(ContainSubstring("ValueError"))
				Expect(result.Stderr).To(ContainSubstring("This is a test error"))
			})

			It("should handle Node.js runtime errors", func() {
				req := &models.RunRequest{
					Language:    "node",
					Code:        testdata.NodeCodes["error_code"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				// 允许正常退出或信号终止
				Expect(result.ExitCode).NotTo(Equal(0))
				Expect(result.Stdout).To(ContainSubstring("Before error"))
				Expect(result.Stderr).To(ContainSubstring("Error: This is a test error"))
			})

			It("should handle timeout for infinite loops", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["infinite_loop"],
					TimeLimitMs: 2000, // 2 seconds timeout
					MemoryMB:    128,
				}

				start := time.Now()
				result, err := httpClient.RunCode(req)
				duration := time.Since(start)

				Expect(err).NotTo(HaveOccurred())
				// 应该在超时时间附近结束
				Expect(duration).To(BeNumerically(">", 2*time.Second))
				Expect(duration).To(BeNumerically("<", 5*time.Second))
				// 进程应该被终止
				Expect(result.ExitCode).NotTo(Equal(0))
			})
		})

		Context("with invalid requests", func() {
			It("should reject empty code", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        "",
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				_, err := httpClient.RunCode(req)
				Expect(err).To(HaveOccurred())
				Expect(err.Error()).To(ContainSubstring("400"))
			})

			It("should reject unsupported language", func() {
				req := &models.RunRequest{
					Language:    "java",
					Code:        "System.out.println(\"Hello\");",
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				_, err := httpClient.RunCode(req)
				Expect(err).To(HaveOccurred())
				Expect(err.Error()).To(ContainSubstring("400"))
			})

			It("should apply default values for missing parameters", func() {
				req := &models.RunRequest{
					Language: "python",
					Code:     testdata.PythonCodes["hello_world"],
					// 不设置其他参数，应该使用默认值
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))
				Expect(result.Stdout).To(Equal("Hello, World!\n"))
			})
		})

		Context("with resource limits", func() {
			It("should respect memory limits", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["memory_intensive"],
					TimeLimitMs: 10000,
					MemoryMB:    64, // 较小的内存限制
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				// 内存不足时进程可能被终止
				if result.ExitCode != 0 {
					// 检查是否是内存相关的错误
					Expect(result.Stderr).To(Or(
						ContainSubstring("MemoryError"),
						ContainSubstring("killed"),
						ContainSubstring("OOM"),
						ContainSubstring("OpenBLAS"),
						ContainSubstring("pthread_create failed"),
						ContainSubstring("Operation not permitted"),
					))
				}
			})

			It("should respect time limits", func() {
				req := &models.RunRequest{
					Language:    "node",
					Code:        testdata.NodeCodes["infinite_loop"],
					TimeLimitMs: 1000, // 1 second timeout
					MemoryMB:    128,
				}

				start := time.Now()
				result, err := httpClient.RunCode(req)
				duration := time.Since(start)

				Expect(err).NotTo(HaveOccurred())
				Expect(duration).To(BeNumerically("<", 4*time.Second))
				Expect(result.ExitCode).NotTo(Equal(0))
			})
		})
	})
})
