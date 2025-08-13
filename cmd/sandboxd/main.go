package main

import (
	"context"
	"flag"
	"log"
	"net/http"
	"os"
	"os/signal"
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

	httpSrv := &http.Server{
		Addr:    *addr,
		Handler: srv.Routes(),
	}

	// start server
	go func() {
		log.Printf("listening on %s", *addr)
		if err := httpSrv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("server error: %v", err)
		}
	}()

	// graceful shutdown
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)
	<-stop
	log.Printf("shutting down...")

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	if err := httpSrv.Shutdown(ctx); err != nil {
		log.Printf("graceful shutdown failed: %v", err)
		_ = httpSrv.Close()
	}
	log.Printf("server stopped")
}
