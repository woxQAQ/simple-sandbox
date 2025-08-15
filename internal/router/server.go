package router

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/woxqaq/simple-sandbox/internal/config"
	"github.com/woxqaq/simple-sandbox/internal/sandbox"
)

type Router struct {
	engine  *gin.Engine
	handler *Handler
	cfg     *config.SandboxConfig
}

func NewServer(mgr sandbox.SandboxManager) *Router {
	// wrap with queue/limit by default
	yamlCfg := config.GetYAMLConfig()

	handler := newHandler(yamlCfg, mgr)

	// 创建 Gin 引擎
	gin.SetMode(gin.ReleaseMode)
	engine := gin.New()

	// 添加中间件
	engine.Use(gin.Logger())
	engine.Use(gin.Recovery())

	server := &Router{
		engine:  engine,
		handler: handler,
		cfg:     yamlCfg,
	}

	server.setupRoutes()
	server.engine.GET("/health", func(ctx *gin.Context) {
		ctx.String(http.StatusOK, "ok")
	})
	return server
}

func (s *Router) setupRoutes() {
	// API 路由组
	v1 := s.engine.Group("/v1")

	// 任务管理端点
	taskGroup := v1.Group("/tasks")
	{
		taskGroup.POST("", s.handler.th.HandleSubmitTask)
		taskGroup.GET("/:id", s.handler.th.HandleGetTaskStatus)
		taskGroup.DELETE("/:id", s.handler.th.HandleCancelTask)
	}

}

// Engine 返回 Gin 引擎实例
func (s *Router) Engine() *gin.Engine {
	return s.engine
}
