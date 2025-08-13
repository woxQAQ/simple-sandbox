package e2e_test

import (
	"encoding/base64"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/woxqaq/simple-sandbox/e2e/testdata"
	"github.com/woxqaq/simple-sandbox/e2e/utils"
	"github.com/woxqaq/simple-sandbox/internal/models"
)

var _ = Describe("Runtime Tests", func() {
	var (
		testServer *utils.TestServer
		httpClient *utils.HTTPClient
	)

	BeforeEach(func() {
		testServer = utils.NewTestServer("8082")
		err := testServer.Start()
		Expect(err).NotTo(HaveOccurred())
		httpClient = utils.NewHTTPClient(testServer.GetBaseURL())
	})

	AfterEach(func() {
		if testServer != nil {
			testServer.Stop()
		}
	})

	Describe("Python Runtime", func() {
		Context("basic functionality", func() {
			It("should execute simple Python code", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        "print('Python is working!')",
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))
				Expect(result.Stdout).To(Equal("Python is working!\n"))
				Expect(result.Stderr).To(BeEmpty())
			})

			It("should handle Python imports", func() {
				code := `
import sys
import os
import json
print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}")
print(f"Platform: {sys.platform}")
print("Imports working correctly")
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
				Expect(result.Stdout).To(ContainSubstring("Python version:"))
				Expect(result.Stdout).To(ContainSubstring("Platform:"))
				Expect(result.Stdout).To(ContainSubstring("Imports working correctly"))
			})

			It("should handle Python exceptions properly", func() {
				code := `
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Caught exception: {e}")
    print("Exception handled successfully")
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
				Expect(result.Stdout).To(ContainSubstring("Caught exception:"))
				Expect(result.Stdout).To(ContainSubstring("division by zero"))
				Expect(result.Stdout).To(ContainSubstring("Exception handled successfully"))
			})
		})

		Context("matplotlib functionality", func() {
			It("should generate matplotlib plots as artifacts", func() {
				req := &models.RunRequest{
					Language:    "python",
					Code:        testdata.PythonCodes["matplotlib_plot"],
					TimeLimitMs: 10000,
					MemoryMB:    256,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))

				// 检查是否生成了图像 artifact
				utils.AssertArtifactExists(result.Artifacts, "image")
				utils.AssertArtifactCount(result.Artifacts, "image", 1)

				// 验证图像数据
				for _, artifact := range result.Artifacts {
					if artifact.Type == "image" {
						// 检查 base64 数据是否有效
						_, err := base64.StdEncoding.DecodeString(artifact.Data)
						Expect(err).NotTo(HaveOccurred())

						// 检查元数据
						Expect(artifact.Metadata).To(HaveKey("format"))
						Expect(artifact.Metadata["format"]).To(Equal("png"))
						Expect(artifact.Metadata).To(HaveKey("index"))
					}
				}
			})

			It("should handle multiple matplotlib plots", func() {
				code := `
import matplotlib.pyplot as plt
import numpy as np

# 创建第一个图表
plt.figure(figsize=(6, 4))
x1 = np.linspace(0, 10, 100)
y1 = np.sin(x1)
plt.plot(x1, y1)
plt.title('Sine Wave')

# 创建第二个图表
plt.figure(figsize=(6, 4))
x2 = np.linspace(0, 10, 100)
y2 = np.cos(x2)
plt.plot(x2, y2)
plt.title('Cosine Wave')

print("Generated two plots")
`
				req := &models.RunRequest{
					Language:    "python",
					Code:        code,
					TimeLimitMs: 10000,
					MemoryMB:    256,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))
				Expect(result.Stdout).To(ContainSubstring("Generated two plots"))

				// 应该生成两个图像 artifacts
				utils.AssertArtifactCount(result.Artifacts, "image", 2)
			})

			It("should handle matplotlib errors gracefully", func() {
				code := `
import matplotlib.pyplot as plt

# 尝试创建无效的图表
try:
    plt.plot([1, 2, 3], [1, 2])  # 长度不匹配
except Exception as e:
    print(f"Matplotlib error handled: {e}")

print("Code execution completed")
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
				Expect(result.Stdout).To(ContainSubstring("Code execution completed"))
			})
		})

		Context("numpy functionality", func() {
			It("should handle numpy operations", func() {
				code := `
import numpy as np

# 基本数组操作
arr1 = np.array([1, 2, 3, 4, 5])
arr2 = np.array([2, 3, 4, 5, 6])
result = arr1 + arr2

print(f"Array 1: {arr1}")
print(f"Array 2: {arr2}")
print(f"Sum: {result}")
print(f"Mean: {np.mean(result)}")
print(f"Std: {np.std(result)}")
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
				Expect(result.Stdout).To(ContainSubstring("Array 1:"))
				Expect(result.Stdout).To(ContainSubstring("Array 2:"))
				Expect(result.Stdout).To(ContainSubstring("Sum:"))
				Expect(result.Stdout).To(ContainSubstring("Mean:"))
				Expect(result.Stdout).To(ContainSubstring("Std:"))
			})
		})
	})

	Describe("Node.js Runtime", func() {
		Context("basic functionality", func() {
			It("should execute simple Node.js code", func() {
				req := &models.RunRequest{
					Language:    "node",
					Code:        "console.log('Node.js is working!');",
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))
				Expect(result.Stdout).To(Equal("Node.js is working!\n"))
				Expect(result.Stderr).To(BeEmpty())
			})

			It("should handle Node.js modules", func() {
				code := `
const fs = require('fs');
const path = require('path');
const os = require('os');

console.log('Node.js version:', process.version);
console.log('Platform:', process.platform);
console.log('Architecture:', process.arch);
console.log('Modules loaded successfully');
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
				Expect(result.Stdout).To(ContainSubstring("Node.js version:"))
				Expect(result.Stdout).To(ContainSubstring("Platform:"))
				Expect(result.Stdout).To(ContainSubstring("Architecture:"))
				Expect(result.Stdout).To(ContainSubstring("Modules loaded successfully"))
			})

			It("should handle Node.js error handling", func() {
				code := `
try {
    const result = JSON.parse('invalid json');
} catch (error) {
    console.log('Caught error:', error.message);
    console.log('Error handled successfully');
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
				Expect(result.Stdout).To(ContainSubstring("Caught error:"))
				Expect(result.Stdout).To(ContainSubstring("Error handled successfully"))
			})
		})

		Context("async functionality", func() {
			It("should handle async/await", func() {
				req := &models.RunRequest{
					Language:    "node",
					Code:        testdata.NodeCodes["async_code"],
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))
				Expect(result.Stdout).To(ContainSubstring("Starting async operation"))
				Expect(result.Stdout).To(ContainSubstring("Async operation completed"))
			})

			It("should handle promises", func() {
				code := `
const promise1 = Promise.resolve('First promise');
const promise2 = Promise.resolve('Second promise');

Promise.all([promise1, promise2])
    .then(results => {
        console.log('All promises resolved:');
        results.forEach((result, index) => {
            console.log('Promise ' + (index + 1) + ': ' + result);
        });
    })
    .catch(error => {
        console.error('Promise error:', error);
    });
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
				Expect(result.Stdout).To(ContainSubstring("All promises resolved"))
				Expect(result.Stdout).To(ContainSubstring("Promise 1: First promise"))
				Expect(result.Stdout).To(ContainSubstring("Promise 2: Second promise"))
			})
		})

		Context("artifacts handling", func() {
			It("should return empty artifacts for Node.js", func() {
				req := &models.RunRequest{
					Language:    "node",
					Code:        "console.log('No artifacts expected');",
					TimeLimitMs: 5000,
					MemoryMB:    128,
				}

				result, err := httpClient.RunCode(req)
				Expect(err).NotTo(HaveOccurred())
				Expect(result.ExitCode).To(Equal(0))
				Expect(result.Artifacts).To(BeEmpty())
			})
		})
	})

	Describe("Cross-runtime comparison", func() {
		It("should produce similar results for equivalent code", func() {
			// Python 版本
			pythonReq := &models.RunRequest{
				Language:    "python",
				Code:        "print('Hello from Python')",
				TimeLimitMs: 5000,
				MemoryMB:    128,
			}

			// Node.js 版本
			nodeReq := &models.RunRequest{
				Language:    "node",
				Code:        "console.log('Hello from Node.js')",
				TimeLimitMs: 5000,
				MemoryMB:    128,
			}

			pythonResult, err := httpClient.RunCode(pythonReq)
			Expect(err).NotTo(HaveOccurred())

			nodeResult, err := httpClient.RunCode(nodeReq)
			Expect(err).NotTo(HaveOccurred())

			// 两者都应该成功执行
			Expect(pythonResult.ExitCode).To(Equal(0))
			Expect(nodeResult.ExitCode).To(Equal(0))

			// 输出应该包含相应的问候语
			Expect(pythonResult.Stdout).To(ContainSubstring("Hello from Python"))
			Expect(nodeResult.Stdout).To(ContainSubstring("Hello from Node.js"))

			// 执行时间应该都很短
			Expect(pythonResult.DurationMs).To(BeNumerically("<", 5000))
			Expect(nodeResult.DurationMs).To(BeNumerically("<", 5000))
		})
	})
})
