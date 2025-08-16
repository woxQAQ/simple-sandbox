package utils

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"time"
)

// TestServer 管理测试服务器的生命周期
type TestServer struct {
	cmd     *exec.Cmd
	baseURL string
	port    string
	config  string
}

// NewTestServer 创建新的测试服务器实例
func NewTestServer(port string) *TestServer {
	return &TestServer{
		port:    port,
		baseURL: fmt.Sprintf("http://localhost:%s", port),
	}
}

// NewTestServerWithConfig 创建带配置文件的测试服务器
func NewTestServerWithConfig(port, config string) *TestServer {
	return &TestServer{
		port:    port,
		baseURL: fmt.Sprintf("http://localhost:%s", port),
		config:  config,
	}
}

// Start 启动测试服务器
func (ts *TestServer) Start() error {
	// 构建服务器二进制文件
	buildCmd := exec.Command("go", "build", "-o", "tmp/sandboxd", "./cmd/sandboxd")
	buildCmd.Dir = filepath.Join("..") // 从 e2e 目录到项目根目录
	if err := buildCmd.Run(); err != nil {
		return fmt.Errorf("failed to build server: %w", err)
	}

	// 启动服务器，增加重试机制
	return ts.startWithRetry(3)
}

// startWithRetry 带重试机制的服务器启动
func (ts *TestServer) startWithRetry(maxRetries int) error {
	var lastErr error

	for i := 0; i < maxRetries; i++ {
		if i > 0 {
			// 等待一段时间再重试
			time.Sleep(time.Duration(i) * 500 * time.Millisecond)
		}

		// 启动服务器
		ts.cmd = exec.Command("tmp/sandboxd", "-addr", ":"+ts.port)
		ts.cmd.Dir = filepath.Join("..") // 从 e2e 目录到项目根目录

		// 设置配置文件环境变量
		configPath := ts.config
		if configPath == "" {
			configPath = "./e2e/config/test_config.yaml"
		}
		// 同时设置 TEST_CONFIG 和 SANDBOX_CONFIG 环境变量
		ts.cmd.Env = append(os.Environ(), "TEST_CONFIG="+configPath, "SANDBOX_CONFIG="+configPath)

		if err := ts.cmd.Start(); err != nil {
			lastErr = fmt.Errorf("failed to start server: %w", err)
			continue
		}

		// 等待服务器启动，减少超时时间以提高重试效率
		err := ts.waitForServer(15 * time.Second)
		if err == nil {
			return nil
		}

		// 如果启动失败，先停止进程再重试
		ts.forceStop()
		lastErr = err
	}

	return fmt.Errorf("failed to start server after %d retries: %w", maxRetries, lastErr)
}

// forceStop 强制停止服务器
func (ts *TestServer) forceStop() {
	if ts.cmd != nil && ts.cmd.Process != nil {
		ts.cmd.Process.Kill()
		ts.cmd.Wait()
	}
}

// Stop 停止测试服务器
func (ts *TestServer) Stop() error {
	if ts.cmd == nil || ts.cmd.Process == nil {
		return nil
	}

	// 检查进程是否还在运行
	if ts.cmd.ProcessState != nil && ts.cmd.ProcessState.Exited() {
		return nil
	}

	// 发送 SIGTERM 信号
	if err := ts.cmd.Process.Signal(syscall.SIGTERM); err != nil {
		// 如果进程已经退出，不算错误
		if strings.Contains(err.Error(), "process already finished") ||
			strings.Contains(err.Error(), "no such process") {
			return nil
		}
		// 如果发送信号失败，尝试直接kill
		return ts.forceStopAndWait()
	}

	// 等待进程结束
	done := make(chan error, 1)
	go func() {
		done <- ts.cmd.Wait()
	}()

	select {
	case err := <-done:
		return err
	case <-time.After(3 * time.Second):
		// 减少等待时间，直接强制杀死进程
		return ts.forceStopAndWait()
	}
}

// forceStopAndWait 强制停止并等待
func (ts *TestServer) forceStopAndWait() error {
	if ts.cmd == nil || ts.cmd.Process == nil {
		return nil
	}

	// 强制杀死进程
	if err := ts.cmd.Process.Kill(); err != nil {
		// 如果进程已经退出，不算错误
		if strings.Contains(err.Error(), "process already finished") ||
			strings.Contains(err.Error(), "no such process") {
			return nil
		}
		// 忽略kill错误，继续等待
	}

	// 等待进程结束
	done := make(chan error, 1)
	go func() {
		done <- ts.cmd.Wait()
	}()

	select {
	case <-done:
		return nil
	case <-time.After(2 * time.Second):
		// 如果进程还没有结束，直接返回
		return nil
	}
}

// waitForServer 等待服务器启动
func (ts *TestServer) waitForServer(timeout time.Duration) error {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return fmt.Errorf("server failed to start within %v", timeout)
		case <-ticker.C:
			resp, err := http.Get(ts.baseURL + "/health")
			if err == nil {
				resp.Body.Close()
				return nil
			}
			// 如果是连接被拒绝，继续等待
			if err != nil && (strings.Contains(err.Error(), "connection refused") ||
				strings.Contains(err.Error(), "no such host")) {
				continue
			}
		}
	}
}

// GetBaseURL 返回服务器的基础 URL
func (ts *TestServer) GetBaseURL() string {
	return ts.baseURL
}
