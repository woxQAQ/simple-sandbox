package models

import (
	"errors"
)

type Language string

const (
	LanguagePython Language = "python"
	LanguageNode   Language = "node"
)

type RunRequest struct {
	Language    Language `json:"language"`
	Code        string   `json:"code"`
	TimeLimitMs int      `json:"time_limit_ms"`
	MemoryMB    int      `json:"memory_mb"`
	CPUShares   int      `json:"cpu_shares"`
	Namespace   string   `json:"namespace"`
}

type RunResult struct {
	ExitCode   int      `json:"exit_code"`
	Stdout     string   `json:"stdout"`
	Stderr     string   `json:"stderr"`
	ImagesB64  []string `json:"images_b64"`
	DurationMs int      `json:"duration_ms"`
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
