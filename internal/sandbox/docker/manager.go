package docker

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	containerTypes "github.com/docker/docker/api/types/container"
	imageTypes "github.com/docker/docker/api/types/image"
	"github.com/docker/docker/api/types/mount"
	"github.com/docker/docker/client"
	"github.com/woxqaq/simple-sandbox/internal/config"
	"github.com/woxqaq/simple-sandbox/internal/logging"
	"github.com/woxqaq/simple-sandbox/internal/models"
	seccomppkg "github.com/woxqaq/simple-sandbox/internal/security/seccomp"
	"go.uber.org/zap"
)

type Manager struct {
	cli *client.Client
}

func New() (*Manager, error) {
	cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
	if err != nil {
		return nil, err
	}
	return &Manager{cli: cli}, nil
}

type runnerJSON struct {
	Stdout    string   `json:"stdout"`
	Stderr    string   `json:"stderr"`
	ImagesB64 []string `json:"images_b64"`
	ExitCode  int      `json:"exit_code"`
}

func (m *Manager) Run(ctx context.Context, req *models.RunRequest) (*models.RunResult, error) {
	if err := req.Validate(); err != nil {
		return nil, err
	}

	image, filename := imageAndFileFor(req.Language)
	if err := m.ensureImage(ctx, image, req.Language); err != nil {
		return nil, fmt.Errorf("ensure image: %w", err)
	}

	tmpDir, err := os.MkdirTemp("", "sandbox-ws-")
	if err != nil {
		return nil, err
	}
	defer os.RemoveAll(tmpDir)

	codePath := filepath.Join(tmpDir, filename)
	if err := os.WriteFile(codePath, []byte(req.Code), 0644); err != nil {
		return nil, err
	}

	workspaceMount := mount.Mount{Type: mount.TypeBind, Source: tmpDir, Target: "/workspace", ReadOnly: true}

	pids := int64(128)
	tmpfsSize := int64(64 * 1024 * 1024)
	tmpfsMode := os.FileMode(01777)

	// Security + resource limits
	hostCfg := &containerTypes.HostConfig{
		Resources: containerTypes.Resources{
			Memory:         int64(req.MemoryMB) * 1024 * 1024,
			CPUShares:      int64(req.CPUShares),
			PidsLimit:      &pids,
			OomKillDisable: func(b bool) *bool { return &b }(false),
		},
		ReadonlyRootfs: true,
		CapDrop:        []string{"ALL"},
		SecurityOpt:    []string{"no-new-privileges", "seccomp=" + seccomppkg.For(req.Language)},
		Mounts: []mount.Mount{
			workspaceMount,
			{Type: mount.TypeTmpfs, Target: "/tmp", TmpfsOptions: &mount.TmpfsOptions{SizeBytes: tmpfsSize, Mode: tmpfsMode}},
			{Type: mount.TypeTmpfs, Target: "/dev/shm", TmpfsOptions: &mount.TmpfsOptions{SizeBytes: int64(8 * 1024 * 1024), Mode: os.FileMode(01777)}},
		},
	}

	cfg := &containerTypes.Config{
		Image:           image,
		WorkingDir:      "/workspace",
		NetworkDisabled: true,
		Env:             []string{"SANDBOX=1"},
	}

	created, err := m.cli.ContainerCreate(ctx, cfg, hostCfg, nil, nil, "")
	if err != nil {
		return nil, err
	}
	containerID := created.ID
	defer func() {
		_ = m.cli.ContainerRemove(context.Background(), containerID, containerTypes.RemoveOptions{Force: true})
	}()

	start := time.Now()
	if err := m.cli.ContainerStart(ctx, containerID, containerTypes.StartOptions{}); err != nil {
		return nil, err
	}

	// enforce time limit
	ctxRun, cancel := context.WithTimeout(ctx, time.Duration(req.TimeLimitMs)*time.Millisecond)
	defer cancel()
	doneCh, errCh := m.cli.ContainerWait(ctxRun, containerID, containerTypes.WaitConditionNotRunning)

	select {
	case <-ctxRun.Done():
		_ = m.cli.ContainerKill(context.Background(), containerID, "KILL")
		return nil, context.DeadlineExceeded
	case err := <-errCh:
		if err != nil {
			return nil, err
		}
	case status := <-doneCh:
		_ = status // we'll read logs for exit code json
	}

	reader, err := m.cli.ContainerLogs(ctx, containerID, containerTypes.LogsOptions{ShowStdout: true, ShowStderr: true})
	if err != nil {
		return nil, err
	}
	defer reader.Close()
	buf := new(bytes.Buffer)
	if _, err := io.Copy(buf, reader); err != nil {
		return nil, err
	}

	parsed, parseErr := parseRunnerJSON(buf.Bytes())
	if parseErr != nil {
		logging.Logger.Warn("failed to parse runner json, returning raw logs", zap.Error(parseErr))
		return &models.RunResult{ExitCode: -1, Stdout: buf.String(), Stderr: "", ImagesB64: nil, DurationMs: int(time.Since(start).Milliseconds())}, nil
	}

	return &models.RunResult{
		ExitCode:   parsed.ExitCode,
		Stdout:     parsed.Stdout,
		Stderr:     parsed.Stderr,
		ImagesB64:  parsed.ImagesB64,
		DurationMs: int(time.Since(start).Milliseconds()),
	}, nil
}

func parseRunnerJSON(raw []byte) (runnerJSON, error) {
	// Docker logs are multiplexed with headers if not using TTY; client usually decodes, but ensure we get pure payload lines
	// Attempt to find last balanced JSON object in the stream
	text := string(raw)
	idx := strings.LastIndex(text, "{")
	if idx == -1 {
		return runnerJSON{}, errors.New("no json found")
	}
	snippet := text[idx:]
	var r runnerJSON
	if err := json.Unmarshal([]byte(snippet), &r); err != nil {
		return runnerJSON{}, err
	}
	return r, nil
}

// ImageRef splits registry/repository and tag

type ImageRef struct {
	Registry   string
	Repository string
	Tag        string
}

func (m *Manager) ensureImage(ctx context.Context, image string, _ string) error {
	_, _, err := m.cli.ImageInspectWithRaw(ctx, image)
	if err == nil {
		return nil
	}
	// auth header if needed
	refParts := strings.SplitN(image, "/", 2)
	server := refParts[0]
	authInfo := config.RegistryAuthFor(server)
	authHeader, _ := config.DockerRegistryAuthHeader(authInfo)
	pullReader, err := m.cli.ImagePull(ctx, image, imageTypes.PullOptions{RegistryAuth: authHeader})
	if err != nil {
		return fmt.Errorf("pull image failed: %w", err)
	}
	io.Copy(io.Discard, pullReader)
	pullReader.Close()
	return nil
}

func imageAndFileFor(lang string) (string, string) {
	full := config.ImageFor(lang)
	switch lang {
	case models.LanguagePython:
		return full, "main.py"
	case models.LanguageNode:
		return full, "main.js"
	default:
		return full, "main"
	}
}
