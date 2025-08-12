package cri

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"os"
	"path/filepath"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	runtimeapi "k8s.io/cri-api/pkg/apis/runtime/v1"

	"github.com/woxqaq/simple-sandbox/internal/config"
	"github.com/woxqaq/simple-sandbox/internal/models"
)

type Manager struct {
	runtime runtimeapi.RuntimeServiceClient
	images  runtimeapi.ImageServiceClient
	socket  string
}

func New() (*Manager, error) {
	sock := os.Getenv("SANDBOX_CRI_SOCKET")
	if sock == "" {
		sock = "unix:///var/run/containerd/containerd.sock"
	}
	conn, err := grpc.NewClient(
		sock,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithContextDialer(func(ctx context.Context, addr string) (net.Conn, error) {
			return net.Dial("unix", addr[len("unix://"):])
		}),
	)
	if err != nil {
		return nil, err
	}
	return &Manager{
		runtime: runtimeapi.NewRuntimeServiceClient(conn),
		images:  runtimeapi.NewImageServiceClient(conn),
		socket:  sock,
	}, nil
}

type runnerJSON struct {
	Stdout    string   `json:"stdout"`
	Stderr    string   `json:"stderr"`
	ImagesB64 []string `json:"images_b64"`
	ExitCode  int      `json:"exit_code"`
}

func (m *Manager) Run(ctx context.Context, req models.RunRequest) (models.RunResult, error) {
	if err := req.Validate(); err != nil {
		return models.RunResult{}, err
	}

	ref := config.ImageRefFor(req.Language)
	image := config.ImageFor(req.Language)

	// ensure image
	authInfo := config.RegistryAuthFor(ref.Registry)
	pullReq := &runtimeapi.PullImageRequest{Image: &runtimeapi.ImageSpec{Image: image}}
	if authInfo.Username != "" || authInfo.IdentityToken != "" || authInfo.Auth != "" {
		pullReq.Auth = &runtimeapi.AuthConfig{
			Username:      authInfo.Username,
			Password:      authInfo.Password,
			Auth:          authInfo.Auth,
			IdentityToken: authInfo.IdentityToken,
			ServerAddress: authInfo.ServerAddress,
		}
	}
	_, err := m.images.PullImage(ctx, pullReq)
	if err != nil {
		return models.RunResult{}, fmt.Errorf("pull image: %w", err)
	}

	// prepare workspace dir
	ws, err := os.MkdirTemp("", "sandbox-cri-")
	if err != nil {
		return models.RunResult{}, err
	}
	defer os.RemoveAll(ws)
	codeFile := "main"
	switch req.Language {
	case models.LanguagePython:
		codeFile = "main.py"
	case models.LanguageNode:
		codeFile = "main.js"
	}
	if err := os.WriteFile(filepath.Join(ws, codeFile), []byte(req.Code), 0644); err != nil {
		return models.RunResult{}, err
	}

	// names
	nameSuffix := randHex(6)
	sandboxName := "sandbox-ps-" + nameSuffix
	containerName := "sandbox-ct-" + nameSuffix

	// pod sandbox with log directory
	podCfg := &runtimeapi.PodSandboxConfig{
		Metadata: &runtimeapi.PodSandboxMetadata{Name: sandboxName, Namespace: req.Namespace},
		Linux: &runtimeapi.LinuxPodSandboxConfig{
			SecurityContext: &runtimeapi.LinuxSandboxSecurityContext{NamespaceOptions: &runtimeapi.NamespaceOption{}},
		},
		LogDirectory: ws,
	}
	sandboxResp, err := m.runtime.RunPodSandbox(ctx, &runtimeapi.RunPodSandboxRequest{Config: podCfg})
	if err != nil {
		return models.RunResult{}, fmt.Errorf("RunPodSandbox: %w", err)
	}
	sandboxID := sandboxResp.PodSandboxId
	defer func() {
		_, _ = m.runtime.StopPodSandbox(context.Background(), &runtimeapi.StopPodSandboxRequest{
			PodSandboxId: sandboxID,
		})
		_, _ = m.runtime.RemovePodSandbox(context.Background(), &runtimeapi.RemovePodSandboxRequest{
			PodSandboxId: sandboxID,
		})
	}()

	// container config
	mem := int64(req.MemoryMB) * 1024 * 1024
	cpuShares := int64(req.CPUShares)
	logPath := "container.log"
	sec := config.SeccompForCRI(req.Language)
	linuxCtx := &runtimeapi.LinuxContainerSecurityContext{
		RunAsUser:      &runtimeapi.Int64Value{Value: 1000},
		ReadonlyRootfs: true,
		NoNewPrivs:     true,
		Capabilities:   &runtimeapi.Capability{DropCapabilities: []string{"ALL"}},
	}
	switch sec.Mode {
	case "unconfined":
		linuxCtx.Seccomp = &runtimeapi.SecurityProfile{ProfileType: runtimeapi.SecurityProfile_Unconfined}
	case "localhost":
		linuxCtx.Seccomp = &runtimeapi.SecurityProfile{ProfileType: runtimeapi.SecurityProfile_Localhost, LocalhostRef: sec.LocalhostRef}
	default:
		linuxCtx.Seccomp = &runtimeapi.SecurityProfile{ProfileType: runtimeapi.SecurityProfile_RuntimeDefault}
	}

	containerCfg := &runtimeapi.ContainerConfig{
		Metadata:   &runtimeapi.ContainerMetadata{Name: containerName},
		Image:      &runtimeapi.ImageSpec{Image: image},
		WorkingDir: "/workspace",
		Linux: &runtimeapi.LinuxContainerConfig{
			Resources:       &runtimeapi.LinuxContainerResources{MemoryLimitInBytes: mem, CpuShares: cpuShares},
			SecurityContext: linuxCtx,
		},
		Mounts:  []*runtimeapi.Mount{{HostPath: ws, ContainerPath: "/workspace", Readonly: true}},
		LogPath: logPath,
	}

	created, err := m.runtime.CreateContainer(ctx, &runtimeapi.CreateContainerRequest{
		PodSandboxId:  sandboxID,
		Config:        containerCfg,
		SandboxConfig: podCfg,
	})
	if err != nil {
		return models.RunResult{}, fmt.Errorf("CreateContainer: %w", err)
	}
	containerID := created.ContainerId
	defer func() {
		_, _ = m.runtime.RemoveContainer(context.Background(), &runtimeapi.RemoveContainerRequest{ContainerId: containerID})
	}()

	if _, err := m.runtime.StartContainer(ctx, &runtimeapi.StartContainerRequest{ContainerId: containerID}); err != nil {
		return models.RunResult{}, fmt.Errorf("StartContainer: %w", err)
	}

	deadline := time.Now().Add(time.Duration(req.TimeLimitMs+2000) * time.Millisecond)
	for {
		st, err := m.runtime.ContainerStatus(ctx, &runtimeapi.ContainerStatusRequest{ContainerId: containerID, Verbose: false})
		if err == nil && st.Status != nil && st.Status.State == runtimeapi.ContainerState_CONTAINER_EXITED {
			break
		}
		if time.Now().After(deadline) {
			_, _ = m.runtime.StopContainer(context.Background(), &runtimeapi.StopContainerRequest{ContainerId: containerID, Timeout: 1})
			return models.RunResult{}, context.DeadlineExceeded
		}
		time.Sleep(200 * time.Millisecond)
	}

	// obtain log path from status (runtime may override)
	st, err := m.runtime.ContainerStatus(ctx, &runtimeapi.ContainerStatusRequest{ContainerId: containerID, Verbose: false})
	if err != nil {
		return models.RunResult{}, fmt.Errorf("ContainerStatus: %w", err)
	}
	logFull := st.Status.LogPath
	if logFull == "" {
		logFull = filepath.Join(ws, logPath)
	}

	f, err := os.Open(logFull)
	if err != nil {
		return models.RunResult{}, fmt.Errorf("open log: %w", err)
	}
	defer f.Close()
	buf := new(bytes.Buffer)
	if _, err := io.Copy(buf, f); err != nil {
		return models.RunResult{}, err
	}

	parsed, perr := parseRunnerJSON(buf.Bytes())
	if perr != nil {
		return models.RunResult{ExitCode: -1, Stdout: buf.String()}, nil
	}
	return models.RunResult{ExitCode: parsed.ExitCode, Stdout: parsed.Stdout, Stderr: parsed.Stderr, ImagesB64: parsed.ImagesB64}, nil
}

func parseRunnerJSON(raw []byte) (runnerJSON, error) {
	idx := bytes.LastIndexByte(raw, '{')
	if idx < 0 {
		return runnerJSON{}, fmt.Errorf("no json")
	}
	var r runnerJSON
	if err := json.Unmarshal(raw[idx:], &r); err != nil {
		return runnerJSON{}, err
	}
	return r, nil
}

func randHex(n int) string {
	b := make([]byte, n)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}
