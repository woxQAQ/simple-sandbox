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

	Describe("/v1/tasks endpoint", func() {
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

		Context("async task management", func() {
			It("should submit task and return task ID", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["hello_world"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
					CPUShares:   256,
				}

				taskResp, err := httpClient.SubmitTask(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(taskResp.TaskID).NotTo(BeEmpty())
				Expect(taskResp.Status).To(Equal(models.TaskStatusPending))
			})

			It("should poll task status until completion", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["hello_world"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
					CPUShares:   256,
				}

				// Submit task
				taskResp, err := httpClient.SubmitTask(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(taskResp.TaskID).NotTo(BeEmpty())

				// Wait for task completion
				status, err := httpClient.WaitForTask(taskResp.TaskID, 10*time.Second)
				Expect(err).NotTo(HaveOccurred())
				Expect(status.Status).To(Equal(models.TaskStatusCompleted))
				Expect(status.Task.Result).NotTo(BeNil())
				Expect(status.Task.Result.ExitCode).To(Equal(0))
				Expect(status.Task.Result.Stdout).To(Equal("Hello, World!\n"))
			})

			It("should handle task status transitions", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["task_status_transition"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
					CPUShares:   256,
				}

				// Submit task
				taskResp, err := httpClient.SubmitTask(req)
				Expect(err).NotTo(HaveOccurred())

				// Check initial status
				status, err := httpClient.GetTaskStatus(taskResp.TaskID)
				Expect(err).NotTo(HaveOccurred())
				// Should be pending or running (goroutine might start quickly)
				Expect(status.Status).To(Or(Equal(models.TaskStatusPending), Equal(models.TaskStatusRunning)))
				Expect(status.Progress).To(BeNumerically(">=", 0.0))

				// Wait for completion
				status, err = httpClient.WaitForTask(taskResp.TaskID, 10*time.Second)
				Expect(err).NotTo(HaveOccurred())
				Expect(status.Status).To(Equal(models.TaskStatusCompleted))
				Expect(status.Progress).To(Equal(100.0))
				Expect(status.Task.Result.Stdout).To(Equal("Done\n"))
			})

			It("should cancel running task", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["task_cancellation"],
					TimeLimitMs: 15000,
					MemoryMB:    128,
					CPUShares:   256,
				}

				// Submit task
				taskResp, err := httpClient.SubmitTask(req)
				Expect(err).NotTo(HaveOccurred())

				// Wait for task to start
				time.Sleep(1 * time.Second)

				// Cancel task
				err = httpClient.CancelTask(taskResp.TaskID)
				Expect(err).NotTo(HaveOccurred())

				// Check status
				status, err := httpClient.GetTaskStatus(taskResp.TaskID)
				Expect(err).NotTo(HaveOccurred())
				Expect(status.Status).To(Equal(models.TaskStatusFailed))
				Expect(status.Task.Error).To(Equal("task cancelled"))
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
				// 应该在超时时间附近结束，允许异步处理的开销
				Expect(duration).To(BeNumerically(">", 2*time.Second))
				Expect(duration).To(BeNumerically("<", 12*time.Second))
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
				// 允许异步处理的开销
				Expect(duration).To(BeNumerically("<", 10*time.Second))
				Expect(result.ExitCode).NotTo(Equal(0))
			})
		})
	})
})
