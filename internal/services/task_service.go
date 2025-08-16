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

	// 创建可取消的 context
	ctx, cancel := context.WithCancel(context.Background())

	task := &models.Task{
		ID:        taskID,
		Status:    models.TaskStatusPending,
		Request:   req,
		CreatedAt: time.Now(),
		CancelFunc: cancel,
	}

	// 存储任务
	s.tasksMu.Lock()
	s.tasks[taskID] = task
	s.tasksMu.Unlock()

	// 在后台执行任务，传入可取消的 context
	go s.executeTask(ctx, task)

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

	// 如果任务已完成或失败，返回错误
	if task.Status == models.TaskStatusCompleted {
		return fmt.Errorf("task already completed")
	}
	if task.Status == models.TaskStatusFailed {
		return fmt.Errorf("task already failed")
	}

	// 调用取消函数来停止执行
	if cancelFunc := task.GetCancelFunc(); cancelFunc != nil {
		cancelFunc()
		task.ClearCancelFunc()
	}

	// 更新任务状态
	task.Status = models.TaskStatusFailed
	task.Error = "task cancelled"
	now := time.Now()
	task.CompletedAt = &now

	if task.Status == models.TaskStatusRunning {
		logging.Logger.Info("running task cancelled", zap.String("task_id", taskID))
	} else {
		logging.Logger.Info("pending task cancelled", zap.String("task_id", taskID))
	}

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
func (s *TaskService) executeTask(ctx context.Context, task *models.Task) {
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

	// 创建带超时的 context，继承父 context 的取消能力
	ctxWithTimeout, cancel := context.WithTimeout(ctx, time.Duration(task.Request.TimeLimitMs)*time.Millisecond)
	defer cancel()

	// 执行任务
	result, err := s.mgr.Run(ctxWithTimeout, task.Request)

	// 清理取消函数
	task.ClearCancelFunc()

	// 更新任务状态
	s.tasksMu.Lock()
	defer s.tasksMu.Unlock()

	// 检查是否已被取消
	if ctx.Err() == context.Canceled {
		// 任务已被取消，不需要更新状态
		return
	}

	completedAt := time.Now()
	task.CompletedAt = &completedAt

	if err != nil {
		if ctxWithTimeout.Err() == context.DeadlineExceeded {
			task.Status = models.TaskStatusTimeout
			task.Error = "execution timeout"
		} else {
			task.Status = models.TaskStatusFailed
			task.Error = err.Error()
		}
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
