package api

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/woxqaq/simple-sandbox/internal/logging"
	"github.com/woxqaq/simple-sandbox/internal/models"
	"github.com/woxqaq/simple-sandbox/internal/sandbox"
	"github.com/woxqaq/simple-sandbox/internal/sandbox/limited"
	"go.uber.org/zap"
)

type Server struct {
	mgr sandbox.SandboxManager
}

func NewServer(mgr sandbox.SandboxManager) *Server {
	// wrap with queue/limit by default
	maxConc := getEnvInt("SANDBOX_MAX_CONCURRENCY", 4)
	maxQueue := getEnvInt("SANDBOX_MAX_QUEUE", 32)
	mgr = limited.NewQueueingManager(mgr, maxConc, maxQueue)
	return &Server{mgr: mgr}
}

func (s *Server) Routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/v1/run", s.handleRun)
	return mux
}

func (s *Server) handleRun(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}
	var req models.RunRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}
	if err := req.Validate(); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), time.Duration(req.TimeLimitMs+2000)*time.Millisecond)
	defer cancel()
	res, err := s.mgr.Run(ctx, req)
	if err != nil {
		if errors.Is(err, limited.ErrQueueFull) {
			w.WriteHeader(http.StatusTooManyRequests)
			_, _ = w.Write([]byte("queue full"))
			return
		}
		logging.Logger.Error("run failed", zap.Error(err))
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(res)
}

func getEnvInt(key string, def int) int {
	v := os.Getenv(key)
	if v == "" {
		return def
	}
	i, err := strconv.Atoi(v)
	if err != nil {
		return def
	}
	return i
}
