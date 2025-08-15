package services

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/woxqaq/simple-sandbox/internal/logging"
	"github.com/woxqaq/simple-sandbox/internal/models"
	"github.com/woxqaq/simple-sandbox/internal/sandbox"
	"go.uber.org/zap"
)

// TaskService 处理任务相关的业务逻辑
type TaskService struct {
	mgr     sandbox.SandboxManager
	tasks   map[string]*models.Task
	tasksMu sync.RWMutex
}

// NewTaskService 创建新的任务服务
func NewTaskService(mgr sandbox.SandboxManager) *TaskService {
	return &TaskService{
		mgr:   mgr,
		tasks: make(map[string]*models.Task),
	}
}

// SubmitTask 提交新任务
func (s *TaskService) SubmitTask(req *models.RunRequest) (*models.Task, error) {
	if err := req.Validate(); err != nil {
		return nil, fmt.Errorf("invalid request: %w", err)
	}

	taskID := uuid.New().String()

	task := &models.Task{
		ID:        taskID,
		Status:    models.TaskStatusPending,
		Request:   req,
		CreatedAt: time.Now(),
	}

	// 存储任务
	s.tasksMu.Lock()
	s.tasks[taskID] = task
	s.tasksMu.Unlock()

	// 在后台执行任务
	go s.executeTask(task)

	return task, nil
}

// GetTask 获取任务信息
func (s *TaskService) GetTask(taskID string) (*models.Task, error) {
	s.tasksMu.RLock()
	defer s.tasksMu.RUnlock()

	task, exists := s.tasks[taskID]
	if !exists {
		return nil, fmt.Errorf("task not found")
	}

	return task, nil
}

// CancelTask 取消任务
func (s *TaskService) CancelTask(taskID string) error {
	s.tasksMu.Lock()
	defer s.tasksMu.Unlock()

	task, exists := s.tasks[taskID]
	if !exists {
		return fmt.Errorf("task not found")
	}

	// 只有正在运行的任务才能取消
	if task.Status == models.TaskStatusRunning {
		task.Status = models.TaskStatusFailed
		task.Error = "task cancelled"
		now := time.Now()
		task.CompletedAt = &now
		logging.Logger.Info("task cancelled", zap.String("task_id", taskID))
		return nil
	}

	// 如果任务已完成或失败，返回错误
	if task.Status == models.TaskStatusCompleted {
		return fmt.Errorf("task already completed")
	}
	if task.Status == models.TaskStatusFailed {
		return fmt.Errorf("task already failed")
	}

	// 如果任务还在等待中，可以取消
	task.Status = models.TaskStatusFailed
	task.Error = "task cancelled"
	now := time.Now()
	task.CompletedAt = &now
	logging.Logger.Info("pending task cancelled", zap.String("task_id", taskID))
	return nil
}

// GetTaskStatus 获取任务状态和进度信息
func (s *TaskService) GetTaskStatus(taskID string) (*models.TaskStatusResponse, error) {
	task, err := s.GetTask(taskID)
	if err != nil {
		return nil, err
	}

	response := &models.TaskStatusResponse{
		Task:   task,
		Status: task.Status,
	}

	// 根据任务状态计算进度
	switch task.Status {
	case models.TaskStatusPending:
		response.Progress = 0.0
		response.Message = "Task is pending execution"
	case models.TaskStatusRunning:
		response.Progress = 50.0
		response.Message = "Task is running"
	case models.TaskStatusCompleted:
		response.Progress = 100.0
		response.Message = "Task completed successfully"
	case models.TaskStatusFailed:
		response.Progress = 100.0
		response.Message = "Task failed"
	case models.TaskStatusTimeout:
		response.Progress = 100.0
		response.Message = "Task timed out"
	}

	return response, nil
}

// executeTask 执行任务
func (s *TaskService) executeTask(task *models.Task) {
	// 更新任务状态为运行中
	s.tasksMu.Lock()
	task.Status = models.TaskStatusRunning
	now := time.Now()
	task.StartedAt = &now
	s.tasksMu.Unlock()

	logging.Logger.Info("async task execution started",
		zap.String("task_id", task.ID),
		zap.String("language", task.Request.Language),
	)

	// 执行任务
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(task.Request.TimeLimitMs)*time.Millisecond)
	defer cancel()

	result, err := s.mgr.Run(ctx, task.Request)

	// 更新任务状态
	s.tasksMu.Lock()
	defer s.tasksMu.Unlock()

	completedAt := time.Now()
	task.CompletedAt = &completedAt

	if err != nil {
		task.Status = models.TaskStatusFailed
		task.Error = err.Error()
		logging.Logger.Error("async task execution failed",
			zap.String("task_id", task.ID),
			zap.Error(err),
		)
	} else if result.ExitCode != 0 {
		task.Status = models.TaskStatusFailed
		task.Error = fmt.Sprintf("execution failed with exit code %d", result.ExitCode)
		task.Result = result
		logging.Logger.Error("async task execution failed",
			zap.String("task_id", task.ID),
			zap.Int("exit_code", result.ExitCode),
		)
	} else {
		task.Status = models.TaskStatusCompleted
		task.Result = result
		logging.Logger.Info("async task execution completed",
			zap.String("task_id", task.ID),
			zap.Int("duration_ms", result.DurationMs),
		)
	}
}

// CleanupTasks 清理已完成的任务（可选的维护操作）
func (s *TaskService) CleanupTasks(olderThan time.Duration) int {
	s.tasksMu.Lock()
	defer s.tasksMu.Unlock()

	cutoff := time.Now().Add(-olderThan)
	count := 0

	for id, task := range s.tasks {
		if task.CompletedAt != nil && task.CompletedAt.Before(cutoff) {
			delete(s.tasks, id)
			count++
		}
	}

	return count
}
