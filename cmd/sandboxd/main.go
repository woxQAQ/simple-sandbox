package main

import (
	"context"
	"flag"
	"net/http"
	"os/signal"
	"syscall"
	"time"

	"github.com/woxqaq/simple-sandbox/internal/config"
	"github.com/woxqaq/simple-sandbox/internal/logging"
	"github.com/woxqaq/simple-sandbox/internal/router"
	"github.com/woxqaq/simple-sandbox/internal/sandbox"
	"go.uber.org/zap"
)

func main() {
	addr := flag.String("addr", ":8080", "HTTP listen address")
	mode := flag.String("ginMode", "release", "Gin mode")
	flag.Parse()

	if err := logging.Init(*mode); err != nil {
		panic(err)
	}
	defer logging.Sync()
	logger := logging.Logger

	if err := config.Init(); err != nil {
		logger.Fatal("load config", zap.Error(err))
	}

	mgr, err := sandbox.NewFromEnv()
	if err != nil {
		logger.Fatal("backend manager", zap.Error(err))
	}

	srv := router.NewServer(mgr, *mode)

	// 创建 HTTP 服务器
	httpServer := &http.Server{
		Addr:    *addr,
		Handler: srv.Engine(),
	}

	// 启动服务器
	go func() {

		logger.Info("listening on", zap.String("addr", *addr))
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatal("server error", zap.Error(err))
		}
	}()

	// 使用 signal.NotifyContext 实现优雅关闭
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	// 等待信号
	<-ctx.Done()
	logger.Info("shutting down...")

	// 创建关闭上下文，给现有请求 30 秒时间完成
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := httpServer.Shutdown(shutdownCtx); err != nil {
		logger.Error("server shutdown error", zap.Error(err))
	}

	logger.Info("server stopped")
}
