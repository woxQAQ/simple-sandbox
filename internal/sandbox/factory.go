package sandbox

import (
	"fmt"
	"os"

	crimgr "github.com/woxqaq/simple-sandbox/internal/sandbox/cri"
	dockermgr "github.com/woxqaq/simple-sandbox/internal/sandbox/docker"
	k8smgr "github.com/woxqaq/simple-sandbox/internal/sandbox/k8s"
)

func NewFromEnv() (SandboxManager, error) {
	b := os.Getenv("SANDBOX_BACKEND")
	if b == "" {
		b = "docker"
	}
	switch b {
	case "docker":
		return dockermgr.New()
	case "cri":
		return crimgr.New()
	case "k8s":
		return k8smgr.New()
	default:
		return nil, fmt.Errorf("unknown backend: %s", b)
	}
}
