package models

import (
	"errors"
)

const (
	LanguagePython = "python"
	LanguageNode   = "node"
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
	Type     string            `json:"type"`     // "image", "file", etc.
	Data     string            `json:"data"`     // Base64 encoded data
	Metadata map[string]string `json:"metadata,omitempty"`
}

type RunResult struct {
	ExitCode   int        `json:"exit_code"`
	Stdout     string     `json:"stdout"`
	Stderr     string     `json:"stderr"`
	Artifacts  []Artifact `json:"artifacts,omitempty"`
	DurationMs int        `json:"duration_ms"`
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
