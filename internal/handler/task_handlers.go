package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/woxqaq/simple-sandbox/internal/models"
	"github.com/woxqaq/simple-sandbox/internal/services"
)

// TaskHandler 处理任务相关的HTTP请求
type TaskHandler struct {
	taskService *services.TaskService
}

// NewTaskHandler 创建新的任务处理器
func NewTaskHandler(taskService *services.TaskService) *TaskHandler {
	return &TaskHandler{
		taskService: taskService,
	}
}

// HandleSubmitTask 处理任务提交请求
func (h *TaskHandler) HandleSubmitTask(c *gin.Context) {
	var req models.RunRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	task, err := h.taskService.SubmitTask(&req)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	response := models.TaskResponse{
		TaskID: task.ID,
		Status: task.Status,
	}

	c.JSON(http.StatusAccepted, response)
}

// HandleGetTaskStatus 处理获取任务状态请求
func (h *TaskHandler) HandleGetTaskStatus(c *gin.Context) {
	taskID := c.Param("id")
	if taskID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "task ID is required"})
		return
	}

	status, err := h.taskService.GetTaskStatus(taskID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, status)
}

// HandleCancelTask 处理任务取消请求
func (h *TaskHandler) HandleCancelTask(c *gin.Context) {
	taskID := c.Param("id")
	if taskID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "task ID is required"})
		return
	}

	if err := h.taskService.CancelTask(taskID); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Task cancelled successfully"})
}
