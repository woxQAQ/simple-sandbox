package utils

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"time"

	. "github.com/onsi/gomega"
	"github.com/woxqaq/simple-sandbox/internal/models"
)

// TestServer 管理测试服务器的生命周期
type TestServer struct {
	cmd     *exec.Cmd
	baseURL string
	port    string
}

// NewTestServer 创建新的测试服务器实例
func NewTestServer(port string) *TestServer {
	return &TestServer{
		port:    port,
		baseURL: fmt.Sprintf("http://localhost:%s", port),
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

	// 启动服务器
	ts.cmd = exec.Command("tmp/sandboxd", "-addr", ":"+ts.port)
	ts.cmd.Dir = filepath.Join("..") // 从 e2e 目录到项目根目录
	ts.cmd.Env = append(os.Environ(), "SANDBOX_CONFIG=./e2e/testdata/test_config.yaml")

	if err := ts.cmd.Start(); err != nil {
		return fmt.Errorf("failed to start server: %w", err)
	}

	// 等待服务器启动
	return ts.waitForServer(30 * time.Second)
}

// Stop 停止测试服务器
func (ts *TestServer) Stop() error {
	if ts.cmd == nil || ts.cmd.Process == nil {
		return nil
	}

	// 发送 SIGTERM 信号
	if err := ts.cmd.Process.Signal(syscall.SIGTERM); err != nil {
		return fmt.Errorf("failed to send SIGTERM: %w", err)
	}

	// 等待进程结束
	done := make(chan error, 1)
	go func() {
		done <- ts.cmd.Wait()
	}()

	select {
	case err := <-done:
		return err
	case <-time.After(15 * time.Second):
		// 强制杀死进程
		if err := ts.cmd.Process.Kill(); err != nil {
			return fmt.Errorf("failed to kill process: %w", err)
		}
		return <-done
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
		}
	}
}

// GetBaseURL 返回服务器的基础 URL
func (ts *TestServer) GetBaseURL() string {
	return ts.baseURL
}

// HTTPClient HTTP 客户端封装
type HTTPClient struct {
	baseURL string
	client  *http.Client
}

// NewHTTPClient 创建新的 HTTP 客户端
func NewHTTPClient(baseURL string) *HTTPClient {
	return &HTTPClient{
		baseURL: baseURL,
		client: &http.Client{
			Timeout: 60 * time.Second, // 增加超时时间以适应长时间运行的测试
		},
	}
}

// RunCode 执行代码请求
func (c *HTTPClient) RunCode(req *models.RunRequest) (*models.RunResult, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.client.Post(
		c.baseURL+"/v1/run",
		"application/json",
		bytes.NewBuffer(body),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result models.RunResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// AssertArtifactExists 断言 artifact 存在
func AssertArtifactExists(artifacts []models.Artifact, artifactType string) {
	found := false
	for _, artifact := range artifacts {
		if artifact.Type == artifactType {
			found = true
			break
		}
	}
	Expect(found).To(BeTrue(), fmt.Sprintf("Expected artifact of type %s to exist", artifactType))
}

// AssertArtifactCount 断言 artifact 数量
func AssertArtifactCount(artifacts []models.Artifact, artifactType string, expectedCount int) {
	count := 0
	for _, artifact := range artifacts {
		if artifact.Type == artifactType {
			count++
		}
	}
	Expect(count).To(Equal(expectedCount), fmt.Sprintf("Expected %d artifacts of type %s, got %d", expectedCount, artifactType, count))
}
