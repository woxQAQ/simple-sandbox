package constants

// Backends
const (
	BackendDocker = "docker"
	BackendPodman = "podman"
	BackendK8s = "k8s"
)

// Images and registries
const (
	DefaultRegistry   = "docker.io"
	DefaultPythonRepo = "sandbox-python"
	DefaultImageTag   = "latest"
)

// Filenames
const (
	PythonMainFile  = "main.py"
	NodeMainFile    = "main.js"
	GenericMainFile = "main"
)

// Common paths
const (
	WorkspaceDir = "/workspace"
	TmpDir       = "/tmp"
	DevShmDir    = "/dev/shm"
)

// Docker runtime settings
const (
	DefaultPidsLimit  = 128
	TmpfsSizeBytes    = 64 * 1024 * 1024
	DevShmSizeBytes   = 8 * 1024 * 1024
	TmpfsModeStickyRW = 01777

	SecurityOptNoNewPrivileges = "no-new-privileges"
	SecurityOptSeccompPrefix   = "seccomp="
	CapDropAll                 = "ALL"
	KillSignal                 = "KILL"

	SandboxEnvKey = "SANDBOX"
	SandboxEnvVal = "1"
)

// K8s defaults
const (
	K8sDefaultNamespace  = "default"
	K8sRunnerContainer   = "runner"
	K8sVolumeCode        = "code"
	K8sVolumeTmp         = "tmp"
	K8sVolumeDShm        = "dshm"
	K8sPollIntervalMs    = 500
	K8sConfigMapNamePref = "sb-code-"
	K8sPodNamePref       = "sb-pod-"
)

//

// Timeouts
const (
	TimeLimitGraceMs = 2000
)
