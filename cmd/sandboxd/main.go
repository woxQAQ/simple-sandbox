package main

import (
	"flag"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/woxqaq/simple-sandbox/internal/api"
	"github.com/woxqaq/simple-sandbox/internal/config"
	"github.com/woxqaq/simple-sandbox/internal/logging"
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

	srv := api.NewServer(mgr)

	// 解析端口
	port := 8080
	if len(*addr) > 0 && (*addr)[0] == ':' {
		if p, err := strconv.Atoi((*addr)[1:]); err == nil {
			port = p
		}
	}

	// 启动服务器
	go func() {
		log.Printf("listening on %s", *addr)
		if err := srv.Start(port); err != nil && err != http.ErrServerClosed {
			log.Fatalf("server error: %v", err)
		}
	}()

	// 优雅关闭
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)
	<-stop
	log.Printf("shutting down...")

	// 给 Gin 服务器一些时间完成现有请求
	time.Sleep(1 * time.Second)
	log.Printf("server stopped")
}
