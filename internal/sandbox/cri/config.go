package cri

import (
	"github.com/woxqaq/simple-sandbox/internal/config"
)

// Config holds CRI-specific configuration
type Config struct {
	// Runtime settings
	Socket  string `yaml:"socket"`
	Backend string `yaml:"backend"`
}

// GetConfig returns CRI configuration from global YAML config
func GetConfig() *Config {
	yamlCfg := config.GetYAMLConfig()

	return &Config{
		Socket:  yamlCfg.Runtime.CRISocket,
		Backend: yamlCfg.Runtime.Backend,
	}
}

// SeccompSetting is the resolved seccomp profile for a language and backend
type SeccompSetting struct {
	Mode         string // runtimeDefault|unconfined|localhost
	LocalhostRef string // for localhost mode
}

// SeccompForCRI returns the CRI seccomp setting for the given language
func (c *Config) SeccompForCRI(lang string) SeccompSetting {
	yamlCfg := config.GetYAMLConfig()
	langSettings, ok := yamlCfg.Languages[lang]
	if !ok {
		langSettings = yamlCfg.Languages["python"] // Fallback to python
	}

	mode := langSettings.Seccomp.CRIMode
	if mode == "" {
		mode = "runtimeDefault"
	}
	return SeccompSetting{
		Mode:         mode,
		LocalhostRef: langSettings.Seccomp.CRILocalhostRef,
	}
}
