package constants

// Backends
const (
	BackendDocker = "docker"
	BackendCRI    = "cri"
	BackendK8s    = "k8s"
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

// CRI defaults
const (
	DefaultCRISocket  = "unix:///var/run/containerd/containerd.sock"
	CRILogFileName    = "container.log"
	CRIPollIntervalMs = 200
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

// Naming prefixes for CRI
const (
	CRIPodSandboxNamePref = "sandbox-ps-"
	CRIContainerNamePref  = "sandbox-ct-"
)

// Timeouts
const (
	TimeLimitGraceMs = 2000
)
