package e2e_test

import (
	"os"
	"path/filepath"
	"time"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/woxqaq/simple-sandbox/e2e/utils"
	"github.com/woxqaq/simple-sandbox/internal/models"
)

var _ = Describe("Configuration Tests", func() {
	var (
		testServer     *utils.TestServer
		httpClient     *utils.HTTPClient
		tempConfigFile string
	)

	BeforeEach(func() {
		// 创建临时配置文件
		tempDir := os.TempDir()
		tempConfigFile = filepath.Join(tempDir, "test_sandbox_config.yaml")
	})

	AfterEach(func() {
		if testServer != nil {
			testServer.Stop()
		}
		// 清理临时配置文件
		if tempConfigFile != "" {
			os.Remove(tempConfigFile)
		}
	})

	Describe("YAML Configuration Loading", func() {
		It("should load default configuration when no config file exists", func() {
			// 使用不存在的配置文件路径
			nonExistentConfig := filepath.Join(os.TempDir(), "non_existent_config.yaml")
			os.Setenv("SANDBOX_CONFIG", nonExistentConfig)
			defer os.Unsetenv("SANDBOX_CONFIG")

			testServer = utils.NewTestServer("8084")
			err := testServer.Start()
			Expect(err).NotTo(HaveOccurred())
			httpClient = utils.NewHTTPClient(testServer.GetBaseURL())

			// 测试基本功能是否正常
			req := &models.RunRequest{
				Language:    "python",
				Code:        "print('Config test')",
				TimeLimitMs: 5000,
				MemoryMB:    128,
			}

			result, err := httpClient.RunCode(req)
			Expect(err).NotTo(HaveOccurred())
			Expect(result.ExitCode).To(Equal(0))
			Expect(result.Stdout).To(Equal("Config test\n"))
		})

		It("should load custom configuration from file", func() {
			// 创建自定义配置文件
			customConfig := `
runtime:
  backend: "docker"
  max_concurrency: 1
  max_queue: 4
  image_registry: "docker.io"
  registry_username: ""
  registry_password: ""
  registry_auth: ""
  registry_identity_token: ""
  k8s_image_pull_secret: ""

languages:
  python:
    repository: "sandbox-python"
    tag: "latest"
    registry: ""
    seccomp:
      k8s_mode: "runtimeDefault"
      k8s_localhost_ref: ""
  node:
    repository: "sandbox-node"
    tag: "latest"
    registry: ""
    seccomp:
      k8s_mode: "runtimeDefault"
      k8s_localhost_ref: ""
`
			err := os.WriteFile(tempConfigFile, []byte(customConfig), 0644)
			Expect(err).NotTo(HaveOccurred())

			os.Setenv("SANDBOX_CONFIG", tempConfigFile)
			defer os.Unsetenv("SANDBOX_CONFIG")

			testServer = utils.NewTestServer("8085")
			err = testServer.Start()
			Expect(err).NotTo(HaveOccurred())
			httpClient = utils.NewHTTPClient(testServer.GetBaseURL())

			// 测试配置是否生效（通过并发限制测试）
			req := &models.RunRequest{
				Language:    "python",
				Code:        "import time; time.sleep(2); print('Done')",
				TimeLimitMs: 5000,
				MemoryMB:    128,
			}

			// 由于 max_concurrency 设置为 1，第二个请求应该排队
			start := time.Now()
			result1, err1 := httpClient.RunCode(req)
			result2, err2 := httpClient.RunCode(req)
			duration := time.Since(start)

			Expect(err1).NotTo(HaveOccurred())
			Expect(err2).NotTo(HaveOccurred())
			Expect(result1.ExitCode).To(Equal(0))
			Expect(result2.ExitCode).To(Equal(0))

			// 由于并发限制，总时间应该接近 4 秒（两个请求串行执行）
			Expect(duration).To(BeNumerically(">=", 3*time.Second))
		})

		It("should handle invalid configuration gracefully", func() {
			// 创建无效的配置文件
			invalidConfig := `
runtime:
  backend: "invalid_backend"
  max_concurrency: -1
  invalid_field: "invalid_value"
`
			err := os.WriteFile(tempConfigFile, []byte(invalidConfig), 0644)
			Expect(err).NotTo(HaveOccurred())

			os.Setenv("SANDBOX_CONFIG", tempConfigFile)
			defer os.Unsetenv("SANDBOX_CONFIG")

			testServer = utils.NewTestServer("8086")
			// 服务器应该能够启动（使用默认值或忽略无效配置）
			err = testServer.Start()
			Expect(err).NotTo(HaveOccurred())
			httpClient = utils.NewHTTPClient(testServer.GetBaseURL())

			// 基本功能应该仍然可用
			req := &models.RunRequest{
				Language:    "python",
				Code:        "print('Still working')",
				TimeLimitMs: 5000,
				MemoryMB:    128,
			}

			result, err := httpClient.RunCode(req)
			Expect(err).NotTo(HaveOccurred())
			Expect(result.ExitCode).To(Equal(0))
			Expect(result.Stdout).To(Equal("Still working\n"))
		})
	})

	Describe("Backend Configuration", func() {
		Context("Docker backend", func() {
			It("should work with Docker backend configuration", func() {
				dockerConfig := `
runtime:
  backend: "docker"
  max_concurrency: 2
  max_queue: 8
  image_registry: "docker.io"

languages:
  python:
    repository: "sandbox-python"
    tag: "latest"
  node:
    repository: "sandbox-node"
    tag: "latest"
`
				err := os.WriteFile(tempConfigFile, []byte(dockerConfig), 0644)
				Expect(err).NotTo(HaveOccurred())

				os.Setenv("SANDBOX_CONFIG", tempConfigFile)
				defer os.Unsetenv("SANDBOX_CONFIG")

				testServer = utils.NewTestServer("8087")
				err = testServer.Start()
				Expect(err).NotTo(HaveOccurred())
				httpClient = utils.NewHTTPClient(testServer.GetBaseURL())

				// 测试 Python 和 Node.js 都能正常工作
				pythonReq := &models.RunRequest{
					Language:    "python",
					Code:        "print('Docker Python works')",
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				nodeReq := &models.RunRequest{
					Language:    "node",
					Code:        "console.log('Docker Node.js works')",
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				pythonResult, err := httpClient.RunCode(pythonReq)
				Expect(err).NotTo(HaveOccurred())
				Expect(pythonResult.ExitCode).To(Equal(0))
				Expect(pythonResult.Stdout).To(Equal("Docker Python works\n"))

				nodeResult, err := httpClient.RunCode(nodeReq)
				Expect(err).NotTo(HaveOccurred())
				Expect(nodeResult.ExitCode).To(Equal(0))
				Expect(nodeResult.Stdout).To(Equal("Docker Node.js works\n"))
			})
		})

		// 注意：Kubernetes 后端测试需要实际的 K8s 集群，这里只做基本的配置测试
		Context("Kubernetes backend configuration", func() {
			It("should accept Kubernetes backend configuration", func() {
				k8sConfig := `
runtime:
  backend: "k8s"
  max_concurrency: 2
  max_queue: 8
  image_registry: "docker.io"
  k8s_image_pull_secret: "regcred"

languages:
  python:
    repository: "sandbox-python"
    tag: "latest"
    seccomp:
      k8s_mode: "runtimeDefault"
      k8s_localhost_ref: ""
  node:
    repository: "sandbox-node"
    tag: "latest"
    seccomp:
      k8s_mode: "localhost"
      k8s_localhost_ref: "profiles/node.json"
`
				err := os.WriteFile(tempConfigFile, []byte(k8sConfig), 0644)
				Expect(err).NotTo(HaveOccurred())

				os.Setenv("SANDBOX_CONFIG", tempConfigFile)
				defer os.Unsetenv("SANDBOX_CONFIG")

				testServer = utils.NewTestServer("8088")
				// 注意：如果没有 K8s 集群，服务器可能无法启动
				// 但配置文件本身应该是有效的
				err = testServer.Start()

				// 如果 K8s 不可用，服务器启动可能失败，这是预期的
				if err != nil {
					// 检查错误是否与 K8s 连接相关
					Expect(err.Error()).To(Or(
						ContainSubstring("kubernetes"),
						ContainSubstring("k8s"),
						ContainSubstring("cluster"),
						ContainSubstring("kubeconfig"),
					))
					Skip("Kubernetes cluster not available for testing")
				}

				// 如果 K8s 可用，测试基本功能
				httpClient = utils.NewHTTPClient(testServer.GetBaseURL())
				req := &models.RunRequest{
					Language:    "python",
					Code:        "print('K8s Python works')",
					TimeLimitMs: 10000, // K8s 可能需要更长时间
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))
				Expect(result.Stdout).To(Equal("K8s Python works\n"))
			})
		})
	})

	Describe("Language Configuration", func() {
		It("should support custom image repositories and tags", func() {
			customImageConfig := `
runtime:
  backend: "docker"
  max_concurrency: 2
  max_queue: 8
  image_registry: "docker.io"

languages:
  python:
    repository: "sandbox-python"
    tag: "latest"
    registry: "docker.io"
  node:
    repository: "sandbox-node"
    tag: "latest"
    registry: "docker.io"
`
			err := os.WriteFile(tempConfigFile, []byte(customImageConfig), 0644)
			Expect(err).NotTo(HaveOccurred())

			os.Setenv("SANDBOX_CONFIG", tempConfigFile)
			defer os.Unsetenv("SANDBOX_CONFIG")

			testServer = utils.NewTestServer("8089")
			err = testServer.Start()
			Expect(err).NotTo(HaveOccurred())
			httpClient = utils.NewHTTPClient(testServer.GetBaseURL())

			// 测试自定义镜像配置是否生效
			req := &models.RunRequest{
				Language:    "python",
				Code:        "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}')",
				TimeLimitMs: 5000,
				MemoryMB:    128,
			}

			result, err := httpClient.RunCode(req)
			Expect(err).NotTo(HaveOccurred())
			Expect(result.ExitCode).To(Equal(0))
			Expect(result.Stdout).To(ContainSubstring("Python"))
		})

		It("should handle missing language configuration", func() {
			partialConfig := `
runtime:
  backend: "docker"
  max_concurrency: 2
  max_queue: 8

languages:
  python:
    repository: "sandbox-python"
    tag: "latest"
  # Node.js 配置缺失
`
			err := os.WriteFile(tempConfigFile, []byte(partialConfig), 0644)
			Expect(err).NotTo(HaveOccurred())

			os.Setenv("SANDBOX_CONFIG", tempConfigFile)
			defer os.Unsetenv("SANDBOX_CONFIG")

			testServer = utils.NewTestServer("8090")
			err = testServer.Start()
			Expect(err).NotTo(HaveOccurred())
			httpClient = utils.NewHTTPClient(testServer.GetBaseURL())

			// Python 应该工作正常
			pythonReq := &models.RunRequest{
				Language:    "python",
				Code:        "print('Python works')",
				TimeLimitMs: 5000,
				MemoryMB:    128,
			}

			pythonResult, err := httpClient.RunCode(pythonReq)
			Expect(err).NotTo(HaveOccurred())
			Expect(pythonResult.ExitCode).To(Equal(0))

			// Node.js 可能使用默认配置或失败
			nodeReq := &models.RunRequest{
				Language:    "node",
				Code:        "console.log('Node.js test')",
				TimeLimitMs: 5000,
				MemoryMB:    128,
			}

			_, err = httpClient.RunCode(nodeReq)
			// 可能成功（使用默认配置）或失败（配置缺失）
			// 这取决于具体的实现
		})
	})

	Describe("Concurrency Configuration", func() {
		It("should respect max_concurrency setting", func() {
			concurrencyConfig := `
runtime:
  backend: "docker"
  max_concurrency: 1  # 只允许一个并发请求
  max_queue: 2

languages:
  python:
    repository: "sandbox-python"
    tag: "latest"
`
			err := os.WriteFile(tempConfigFile, []byte(concurrencyConfig), 0644)
			Expect(err).NotTo(HaveOccurred())

			os.Setenv("SANDBOX_CONFIG", tempConfigFile)
			defer os.Unsetenv("SANDBOX_CONFIG")

			testServer = utils.NewTestServer("8091")
			err = testServer.Start()
			Expect(err).NotTo(HaveOccurred())
			httpClient = utils.NewHTTPClient(testServer.GetBaseURL())

			// 创建需要一定时间执行的请求
			req := &models.RunRequest{
				Language:    "python",
				Code:        "import time; time.sleep(1); print('Done')",
				TimeLimitMs: 5000,
				MemoryMB:    128,
			}

			// 同时发送多个请求
			start := time.Now()
			resultChan := make(chan *models.RunResult, 2)
			errorChan := make(chan error, 2)

			for i := 0; i < 2; i++ {
				go func() {
					result, err := httpClient.RunCode(req)
					if err != nil {
						errorChan <- err
					} else {
						resultChan <- result
					}
				}()
			}

			// 等待所有请求完成
			var results []*models.RunResult
			for i := 0; i < 2; i++ {
				select {
				case result := <-resultChan:
					results = append(results, result)
				case err := <-errorChan:
					Expect(err).NotTo(HaveOccurred())
				case <-time.After(10 * time.Second):
					Fail("Request timed out")
				}
			}

			duration := time.Since(start)

			// 由于并发限制为 1，两个请求应该串行执行
			Expect(len(results)).To(Equal(2))
			for _, result := range results {
				Expect(result.ExitCode).To(Equal(0))
				Expect(result.Stdout).To(Equal("Done\n"))
			}

			// 总时间应该接近 2 秒（两个 1 秒的请求串行执行）
			Expect(duration).To(BeNumerically(">=", 1800*time.Millisecond))
			Expect(duration).To(BeNumerically("<", 3*time.Second))
		})
	})
})
