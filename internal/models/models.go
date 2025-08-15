package models

import (
	"errors"
	"time"
)

const (
	LanguagePython = "python"
	LanguageNode   = "node"
	
	TaskStatusPending   = "pending"
	TaskStatusRunning   = "running"
	TaskStatusCompleted = "completed"
	TaskStatusFailed    = "failed"
	TaskStatusTimeout   = "timeout"
)

type RunRequest struct {
	Language    string `json:"language"`
	Code        string `json:"code"`
	TimeLimitMs int    `json:"time_limit_ms"`
	MemoryMB    int    `json:"memory_mb"`
	CPUShares   int    `json:"cpu_shares"`
	Namespace   string `json:"namespace"`
}

type Artifact struct {
	Type     string            `json:"type"` // "image", "file", etc.
	Data     string            `json:"data"` // Base64 encoded data
	Metadata map[string]string `json:"metadata,omitempty"`
}

type RunResult struct {
	ExitCode   int        `json:"exit_code"`
	Stdout     string     `json:"stdout"`
	Stderr     string     `json:"stderr"`
	Artifacts  []Artifact `json:"artifacts,omitempty"`
	DurationMs int        `json:"duration_ms"`
}

// Task represents an asynchronous execution task
type Task struct {
	ID          string     `json:"id"`
	Status      string     `json:"status"`
	Request     *RunRequest `json:"request"`
	Result      *RunResult `json:"result,omitempty"`
	Error       string     `json:"error,omitempty"`
	CreatedAt   time.Time  `json:"created_at"`
	StartedAt   *time.Time `json:"started_at,omitempty"`
	CompletedAt *time.Time `json:"completed_at,omitempty"`
}

// TaskResponse is the immediate response when submitting a task
type TaskResponse struct {
	TaskID string `json:"task_id"`
	Status string `json:"status"`
}

// TaskStatusRequest is the request to poll task status
type TaskStatusRequest struct {
	TaskID string `json:"task_id"`
}

// TaskStatusResponse is the response for task status polling
type TaskStatusResponse struct {
	Task      *Task     `json:"task"`
	Status    string    `json:"status"`
	Progress  float64   `json:"progress,omitempty"`
	Message   string    `json:"message,omitempty"`
}

func (r *RunRequest) Validate() error {
	if r.Code == "" {
		return errors.New("code is required")
	}
	switch r.Language {
	case LanguagePython, LanguageNode:
		// ok
	default:
		return errors.New("unsupported language")
	}
	if r.TimeLimitMs <= 0 {
		r.TimeLimitMs = 10000
	}
	if r.MemoryMB <= 0 {
		r.MemoryMB = 512
	}
	if r.CPUShares <= 0 {
		r.CPUShares = 256
	}
	if r.Namespace == "" {
		r.Namespace = "default"
	}
	return nil
}
