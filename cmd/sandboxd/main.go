package main

import (
	"context"
	"flag"
	"log"
	"net/http"
	"os/signal"
	"syscall"
	"time"

	"github.com/woxqaq/simple-sandbox/internal/config"
	"github.com/woxqaq/simple-sandbox/internal/logging"
	"github.com/woxqaq/simple-sandbox/internal/router"
	"github.com/woxqaq/simple-sandbox/internal/sandbox"
)

func main() {
	addr := flag.String("addr", ":8080", "HTTP listen address")
	flag.Parse()

	if err := logging.Init(); err != nil {
		log.Fatalf("init logger: %v", err)
	}
	defer logging.Sync()

	if err := config.Init(); err != nil {
		log.Fatalf("load config: %v", err)
	}

	mgr, err := sandbox.NewFromEnv()
	if err != nil {
		log.Fatalf("backend manager: %v", err)
	}

	srv := router.NewServer(mgr)

	// 创建 HTTP 服务器
	httpServer := &http.Server{
		Addr:    *addr,
		Handler: srv.Engine(),
	}

	// 启动服务器
	go func() {
		log.Printf("listening on %s", *addr)
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("server error: %v", err)
		}
	}()

	// 使用 signal.NotifyContext 实现优雅关闭
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	// 等待信号
	<-ctx.Done()
	log.Printf("shutting down...")

	// 创建关闭上下文，给现有请求 30 秒时间完成
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := httpServer.Shutdown(shutdownCtx); err != nil {
		log.Printf("server shutdown error: %v", err)
	}

	log.Printf("server stopped")
}
