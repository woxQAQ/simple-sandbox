package main

import (
	"flag"
	"log"
	"net/http"

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
	log.Printf("listening on %s", *addr)
	if err := http.ListenAndServe(*addr, srv.Routes()); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
