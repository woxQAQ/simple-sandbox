package router

import (
	"github.com/woxqaq/simple-sandbox/internal/config"
	"github.com/woxqaq/simple-sandbox/internal/handler"
	"github.com/woxqaq/simple-sandbox/internal/sandbox"
	"github.com/woxqaq/simple-sandbox/internal/sandbox/limited"
	"github.com/woxqaq/simple-sandbox/internal/services"
)

type Handler struct {
	th *handler.TaskHandler
}

func newHandler(cfg *config.SandboxConfig, mgr sandbox.SandboxManager) *Handler {
	// 创建认证管理器
	maxConcurrency := cfg.Runtime.MaxConcurrency
	if maxConcurrency == 0 {
		maxConcurrency = 4 // Default concurrency
	}
	maxQueue := cfg.Runtime.MaxQueue
	if maxQueue == 0 {
		maxQueue = 32 // Default queue size
	}
	mgr = limited.NewQueueingManager(mgr, maxConcurrency, maxQueue)

	taskService := services.NewTaskService(mgr)
	taskHandler := handler.NewTaskHandler(taskService)

	return &Handler{
		th: taskHandler,
	}
}
