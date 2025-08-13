package podman

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"go.uber.org/zap"

	"github.com/woxqaq/simple-sandbox/internal/constants"
	"github.com/woxqaq/simple-sandbox/internal/logging"
	"github.com/woxqaq/simple-sandbox/internal/models"
	"github.com/woxqaq/simple-sandbox/internal/sandbox/common"
	seccomppkg "github.com/woxqaq/simple-sandbox/internal/security/seccomp"
)

type Manager struct {
	// Podman doesn't have an official Go client, so we use CLI commands
}

func New() (*Manager, error) {
	// Check if podman is available
	if _, err := exec.LookPath("podman"); err != nil {
		return nil, fmt.Errorf("podman not found in PATH: %w", err)
	}
	return &Manager{}, nil
}

func (m *Manager) Run(ctx context.Context, req *models.RunRequest) (*models.RunResult, error) {
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
	if err = os.WriteFile(codePath, []byte(req.Code), 0644); err != nil {
		return nil, err
	}

	// Build podman run command
	args := []string{
		"run",
		"--rm",
		"--read-only",
		"--network=none",
		"--cap-drop=ALL",
		"--security-opt=no-new-privileges",
		fmt.Sprintf("--security-opt=seccomp=%s", seccomppkg.For(req.Language)),
		fmt.Sprintf("--memory=%dm", req.MemoryMB),
		fmt.Sprintf("--cpu-shares=%d", req.CPUShares),
		fmt.Sprintf("--pids-limit=%d", constants.DefaultPidsLimit),
		"--oom-kill-disable=false",
		fmt.Sprintf("--volume=%s:%s:ro,Z", tmpDir, constants.WorkspaceDir),
		fmt.Sprintf("--tmpfs=%s:size=%d,mode=%o", constants.TmpDir, constants.TmpfsSizeBytes, constants.TmpfsModeStickyRW),
		fmt.Sprintf("--tmpfs=%s:size=%d,mode=%o", constants.DevShmDir, constants.DevShmSizeBytes, constants.TmpfsModeStickyRW),
		fmt.Sprintf("--workdir=%s", constants.WorkspaceDir),
		fmt.Sprintf("--env=%s=%s", constants.SandboxEnvKey, constants.SandboxEnvVal),
		image,
	}

	start := time.Now()
	ctxRun, cancel := context.WithTimeout(ctx, time.Duration(req.TimeLimitMs)*time.Millisecond)
	defer cancel()

	cmd := exec.CommandContext(ctxRun, "podman", args...)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err = cmd.Run()
	duration := time.Since(start)

	if ctxRun.Err() == context.DeadlineExceeded {
		return nil, context.DeadlineExceeded
	}

	// Combine stdout and stderr for parsing
	output := stdout.String() + stderr.String()

	parsed, parseErr := common.ParseRunnerJSONFromBytes([]byte(output))
	if parseErr != nil {
		logging.Logger.Warn("failed to parse runner json, returning raw logs", zap.Error(parseErr))
		return &models.RunResult{
			ExitCode:   getExitCode(err),
			Stdout:     stdout.String(),
			Stderr:     stderr.String(),
			Artifacts:  nil,
			DurationMs: int(duration.Milliseconds()),
		}, nil
	}

	return &models.RunResult{
		ExitCode:   parsed.ExitCode,
		Stdout:     parsed.Stdout,
		Stderr:     parsed.Stderr,
		Artifacts:  parsed.Artifacts,
		DurationMs: int(duration.Milliseconds()),
	}, nil
}

func (m *Manager) ensureImage(ctx context.Context, image string, lang string) error {
	// Check if image exists locally
	cmd := exec.CommandContext(ctx, "podman", "image", "exists", image)
	if err := cmd.Run(); err == nil {
		return nil // Image exists
	}

	// Pull image with authentication if configured
	podmanConfig := GetConfig()
	refParts := strings.SplitN(image, "/", 2)
	server := refParts[0]
	authInfo := podmanConfig.RegistryAuthFor(server)

	pullArgs := []string{"pull"}
	if authInfo.Username != "" && authInfo.Password != "" {
		pullArgs = append(pullArgs, "--creds", fmt.Sprintf("%s:%s", authInfo.Username, authInfo.Password))
	}
	pullArgs = append(pullArgs, image)

	cmd = exec.CommandContext(ctx, "podman", pullArgs...)
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("pull image failed: %w", err)
	}
	return nil
}

func imageAndFileFor(lang string) (string, string) {
	full := common.ImageFor(lang)
	switch lang {
	case models.LanguagePython:
		return full, "main.py"
	case models.LanguageNode:
		return full, "main.js"
	default:
		return full, "main"
	}
}

func getExitCode(err error) int {
	if err == nil {
		return 0
	}
	if exitError, ok := err.(*exec.ExitError); ok {
		return exitError.ExitCode()
	}
	return -1
}