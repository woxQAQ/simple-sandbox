package utils

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/woxqaq/simple-sandbox/internal/models"
)

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

// SubmitTask 提交异步任务
func (c *HTTPClient) SubmitTask(req *models.RunRequest) (*models.TaskResponse, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := c.client.Post(
		c.baseURL+"/v1/tasks",
		"application/json",
		bytes.NewBuffer(body),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusAccepted {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result models.TaskResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// GetTaskStatus 获取任务状态
func (c *HTTPClient) GetTaskStatus(taskID string) (*models.TaskStatusResponse, error) {
	resp, err := c.client.Get(c.baseURL + "/v1/tasks/" + taskID)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result models.TaskStatusResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}

// CancelTask 取消任务
func (c *HTTPClient) CancelTask(taskID string) error {
	req, err := http.NewRequest("DELETE", c.baseURL+"/v1/tasks/"+taskID, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(body))
	}

	return nil
}

// WaitForTask 等待任务完成
func (c *HTTPClient) WaitForTask(taskID string, timeout time.Duration) (*models.TaskStatusResponse, error) {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return nil, fmt.Errorf("task did not complete within %v", timeout)
		case <-ticker.C:
			status, err := c.GetTaskStatus(taskID)
			if err != nil {
				return nil, err
			}

			if status.Status == models.TaskStatusCompleted || status.Status == models.TaskStatusFailed {
				return status, nil
			}
		}
	}
}

// RunCode 执行代码请求（同步方式，用于向后兼容）
func (c *HTTPClient) RunCode(req *models.RunRequest) (*models.RunResult, error) {
	// 提交任务
	taskResp, err := c.SubmitTask(req)
	if err != nil {
		return nil, err
	}

	// 等待任务完成
	status, err := c.WaitForTask(taskResp.TaskID, 60*time.Second)
	if err != nil {
		return nil, err
	}

	if status.Task.Result == nil {
		return nil, fmt.Errorf("task completed but no result available")
	}

	return status.Task.Result, nil
}