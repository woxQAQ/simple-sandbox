package sandbox

import (
	"fmt"

	"github.com/woxqaq/simple-sandbox/internal/config"
	"github.com/woxqaq/simple-sandbox/internal/constants"
	dockermgr "github.com/woxqaq/simple-sandbox/internal/sandbox/docker"
	k8smgr "github.com/woxqaq/simple-sandbox/internal/sandbox/k8s"
)

func NewFromEnv() (SandboxManager, error) {
	yamlCfg := config.GetYAMLConfig()
	b := yamlCfg.Runtime.Backend
	if b == "" {
		b = constants.BackendDocker // default backend
	}
	switch b {
	case constants.BackendDocker:
		return dockermgr.New()
	case constants.BackendK8s:
		return k8smgr.New()
	default:
		return nil, fmt.Errorf("unknown backend: %s", b)
	}
}
