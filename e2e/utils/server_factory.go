package utils

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// CreateTestServerWithDynamicPort 创建使用动态端口的服务器
func CreateTestServerWithDynamicPort() (*TestServer, error) {
	return createTestServerWithRetry("", 3)
}

// CreateTestServerWithDynamicPortAndConfig 创建使用动态端口和配置的服务器
func CreateTestServerWithDynamicPortAndConfig(config string) (*TestServer, error) {
	return createTestServerWithRetry(config, 3)
}

// CreateConfiguredTestServer 创建使用配置文件的测试服务器
func CreateConfiguredTestServer() (*TestServer, *HTTPClient, error) {
	// 获取配置文件路径
	configPath := getConfigFromEnvironment()

	// 获取动态端口
	port := getDynamicPort()

	// 创建测试服务器
	server := NewTestServerWithConfig(port, configPath)

	// 启动服务器
	if err := server.Start(); err != nil {
		return nil, nil, fmt.Errorf("failed to start test server: %w", err)
	}

	// 创建HTTP客户端
	client := NewHTTPClient(server.GetBaseURL())

	return server, client, nil
}

// createTestServerWithRetry 带重试机制的服务器创建
func createTestServerWithRetry(config string, maxRetries int) (*TestServer, error) {
	var lastErr error

	for i := 0; i < maxRetries; i++ {
		if i > 0 {
			// 等待一段时间再重试
			time.Sleep(time.Duration(i) * 300 * time.Millisecond)
		}

		port := getDynamicPort()
		var server *TestServer

		if config != "" {
			server = NewTestServerWithConfig(port, config)
		} else {
			server = NewTestServer(port)
		}

		// 启动服务器
		err := server.Start()
		if err == nil {
			return server, nil
		}

		// 如果启动失败，清理资源
		if server != nil {
			server.Stop()
		}
		lastErr = err

		// 如果是端口相关错误，继续重试
		if strings.Contains(err.Error(), "address already in use") ||
			strings.Contains(err.Error(), "bind") ||
			strings.Contains(err.Error(), "failed to start") {
			continue
		}

		// 其他错误直接返回
		break
	}

	return nil, fmt.Errorf("failed to create test server after %d retries: %w", maxRetries, lastErr)
}

// ReleaseTestServer 释放测试服务器资源
func ReleaseTestServer(server *TestServer) error {
	var err error

	// 停止服务器
	if server != nil {
		err = server.Stop()
	}

	// 端口会自动释放，无需显式管理

	return err
}

// NewBuildCommand 创建构建命令
func NewBuildCommand() *exec.Cmd {
	buildCmd := exec.Command("go", "build", "-o", "tmp/sandboxd", "./cmd/sandboxd")
	buildCmd.Dir = filepath.Join("..") // 从 e2e 目录到项目根目录
	return buildCmd
}

// getDynamicPort 为并行测试生成动态端口
func getDynamicPort() string {
	// 获取Ginkgo并行进程ID
	ginkgoParallelProcess := os.Getenv("GINKGO_PARALLEL_PROCESS")
	if ginkgoParallelProcess == "" {
		ginkgoParallelProcess = "0"
	}

	// 获取进程ID并计算端口
	pid := os.Getpid()
	processNum, _ := strconv.Atoi(ginkgoParallelProcess)

	// 基础端口8081，每个进程分配200端口范围
	basePort := 8081
	portRange := 200
	port := basePort + (processNum * portRange) + (pid % 50)

	// 确保端口在合理范围内
	maxPort := basePort + (16 * portRange) + 50
	if port > maxPort {
		port = basePort + (pid % 50)
	}

	return strconv.Itoa(port)
}