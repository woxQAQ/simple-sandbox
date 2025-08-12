package api

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/woxqaq/simple-sandbox/internal/models"
)

type fakeMgr struct {
	res models.RunResult
	err error
}

func (f *fakeMgr) Run(ctx context.Context, req models.RunRequest) (models.RunResult, error) {
	return f.res, f.err
}

func TestRunHandler_OK(t *testing.T) {
	s := NewServer(&fakeMgr{res: models.RunResult{ExitCode: 0, Stdout: "ok"}})
	reqBody, _ := json.Marshal(models.RunRequest{Language: models.LanguageNode, Code: "console.log('hi')"})
	r := httptest.NewRequest(http.MethodPost, "/v1/run", bytes.NewReader(reqBody))
	w := httptest.NewRecorder()
	s.Routes().ServeHTTP(w, r)
	if w.Code != http.StatusOK {
		t.Fatalf("status = %d", w.Code)
	}
	var got models.RunResult
	if err := json.Unmarshal(w.Body.Bytes(), &got); err != nil {
		t.Fatalf("json: %v", err)
	}
	if got.ExitCode != 0 || got.Stdout != "ok" {
		t.Fatalf("unexpected response: %+v", got)
	}
}
