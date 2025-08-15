package api

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/woxqaq/simple-sandbox/internal/auth"
	"github.com/woxqaq/simple-sandbox/internal/config"
	"github.com/woxqaq/simple-sandbox/internal/logging"
	"github.com/woxqaq/simple-sandbox/internal/models"
	"github.com/woxqaq/simple-sandbox/internal/sandbox"
	"github.com/woxqaq/simple-sandbox/internal/sandbox/limited"
	"go.uber.org/zap"
)

type Server struct {
	mgr     sandbox.SandboxManager
	auth    *auth.AuthManager
	useAuth bool
	engine  *gin.Engine
}

func NewServer(mgr sandbox.SandboxManager) *Server {
	// wrap with queue/limit by default
	yamlCfg := config.GetYAMLConfig()
	maxConcurrency := yamlCfg.Runtime.MaxConcurrency
	if maxConcurrency == 0 {
		maxConcurrency = 4 // Default concurrency
	}
	maxQueue := yamlCfg.Runtime.MaxQueue
	if maxQueue == 0 {
		maxQueue = 32 // Default queue size
	}
	mgr = limited.NewQueueingManager(mgr, maxConcurrency, maxQueue)
	
	// 创建认证管理器
	authMgr := auth.NewAuthManager("your-secret-key-change-in-production", 24*time.Hour)
	
	// 检查是否启用认证
	useAuth := yamlCfg.Security != nil && yamlCfg.Security.EnableAuth
	
	// 创建 Gin 引擎
	gin.SetMode(gin.ReleaseMode)
	engine := gin.New()
	
	// 添加中间件
	engine.Use(gin.Logger())
	engine.Use(gin.Recovery())
	
	server := &Server{
		mgr:     mgr,
		auth:    authMgr,
		useAuth: useAuth,
		engine:  engine,
	}
	
	server.setupRoutes()
	return server
}

func (s *Server) setupRoutes() {
	// 健康检查
	s.engine.GET("/health", s.handleHealth)
	
	// API 路由组
	v1 := s.engine.Group("/v1")
	
	// 认证端点（仅在启用认证时）
	if s.useAuth {
		v1.POST("/auth/token", s.handleGenerateToken)
	}
	
	// 代码执行端点
	runGroup := v1.Group("/run")
	if s.useAuth {
		runGroup.Use(s.auth.Middleware())
	}
	runGroup.POST("", s.handleRun)
}

func (s *Server) handleHealth(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "healthy",
		"time":   time.Now().Format(time.RFC3339),
	})
}

func (s *Server) handleGenerateToken(c *gin.Context) {
	// 生成新的认证令牌
	token, err := s.auth.GenerateToken()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate token"})
		return
	}
	
	// 返回令牌给客户端
	c.JSON(http.StatusOK, gin.H{
		"token": token,
		"type":  "Bearer",
		"expires_in": int64(24 * time.Hour.Seconds()),
	})
}

func (s *Server) handleRun(c *gin.Context) {
	var req models.RunRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	
	if err := req.Validate(); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	
	// Don't set timeout at API server level - let the podman manager handle timeouts
	// This ensures consistent timeout behavior and allows the manager to return proper RunResult for timeouts
	ctx := c.Request.Context()
	
	logging.Logger.Info("starting run", zap.Int("time_limit_ms", req.TimeLimitMs))
	res, err := s.mgr.Run(ctx, &req)
	if err != nil {
		logging.Logger.Error("run failed", zap.Error(err), zap.String("error_type", "context_error"))
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	
	c.JSON(http.StatusOK, res)
}

// Engine 返回 Gin 引擎实例
func (s *Server) Engine() *gin.Engine {
	return s.engine
}
