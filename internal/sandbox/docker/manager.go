package docker

import (
	"bytes"
	"context"
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
	"go.uber.org/zap"

	"github.com/woxqaq/simple-sandbox/internal/constants"
	"github.com/woxqaq/simple-sandbox/internal/logging"
	"github.com/woxqaq/simple-sandbox/internal/models"
	"github.com/woxqaq/simple-sandbox/internal/sandbox/common"
	seccomppkg "github.com/woxqaq/simple-sandbox/internal/security/seccomp"
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

	workspaceMount := mount.Mount{Type: mount.TypeBind, Source: tmpDir, Target: "/workspace", ReadOnly: true}

	pids := int64(constants.DefaultPidsLimit)
	tmpfsSize := int64(constants.TmpfsSizeBytes)
	tmpfsMode := os.FileMode(constants.TmpfsModeStickyRW)

	// Security + resource limits
	hostCfg := &containerTypes.HostConfig{
		Resources: containerTypes.Resources{
			Memory:         int64(req.MemoryMB) * 1024 * 1024,
			CPUShares:      int64(req.CPUShares),
			PidsLimit:      &pids,
			OomKillDisable: func(b bool) *bool { return &b }(false),
		},
		ReadonlyRootfs: true,
		CapDrop:        []string{constants.CapDropAll},
		SecurityOpt:    []string{constants.SecurityOptNoNewPrivileges, constants.SecurityOptSeccompPrefix + seccomppkg.For(req.Language)},
		Mounts: []mount.Mount{
			workspaceMount,
			{
				Type:         mount.TypeTmpfs,
				Target:       constants.TmpDir,
				TmpfsOptions: &mount.TmpfsOptions{SizeBytes: tmpfsSize, Mode: tmpfsMode},
			},
			{
				Type:   mount.TypeTmpfs,
				Target: constants.DevShmDir,
				TmpfsOptions: &mount.TmpfsOptions{
					SizeBytes: int64(constants.DevShmSizeBytes),
					Mode:      os.FileMode(constants.TmpfsModeStickyRW),
				},
			},
		},
	}

	cfg := &containerTypes.Config{
		Image:           image,
		WorkingDir:      constants.WorkspaceDir,
		NetworkDisabled: true,
		Env:             []string{constants.SandboxEnvKey + "=" + constants.SandboxEnvVal},
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
	if err = m.cli.ContainerStart(ctx, containerID, containerTypes.StartOptions{}); err != nil {
		return nil, err
	}

	// Enforce time limit by wrapping ContainerWait with a context timeout
	ctxRun, cancel := context.WithTimeout(ctx, time.Duration(req.TimeLimitMs)*time.Millisecond)
	defer cancel()
	doneCh, errCh := m.cli.ContainerWait(ctxRun, containerID, containerTypes.WaitConditionNotRunning)

	select {
	case <-ctxRun.Done():
		_ = m.cli.ContainerKill(context.Background(), containerID, constants.KillSignal)
		return nil, context.DeadlineExceeded
	case err = <-errCh:
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

	parsed, parseErr := common.ParseRunnerJSONFromBytes(buf.Bytes())
	if parseErr != nil {
		logging.Logger.Warn("failed to parse runner json, returning raw logs", zap.Error(parseErr))
		return &models.RunResult{ExitCode: -1, Stdout: buf.String(), Stderr: "", Artifacts: nil, DurationMs: int(time.Since(start).Milliseconds())}, nil
	}

	return &models.RunResult{
		ExitCode:   parsed.ExitCode,
		Stdout:     parsed.Stdout,
		Stderr:     parsed.Stderr,
		Artifacts:  parsed.Artifacts,
		DurationMs: int(time.Since(start).Milliseconds()),
	}, nil
}

func (m *Manager) ensureImage(ctx context.Context, image string, lang string) error {
	_, _, err := m.cli.ImageInspectWithRaw(ctx, image)
	if err == nil {
		return nil
	}

	// Get Docker config for authentication
	dockerConfig := GetConfig()
	refParts := strings.SplitN(image, "/", 2)
	server := refParts[0]
	authInfo := dockerConfig.RegistryAuthFor(server)
	authHeader, _ := authInfo.DockerRegistryAuthHeader()

	pullReader, err := m.cli.ImagePull(ctx, image, imageTypes.PullOptions{
		RegistryAuth: authHeader,
	})
	if err != nil {
		return fmt.Errorf("pull image failed: %w", err)
	}
	io.Copy(io.Discard, pullReader)
	pullReader.Close()
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
