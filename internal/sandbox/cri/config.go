package cri

import (
	"github.com/woxqaq/simple-sandbox/internal/config"
)

// Config holds CRI-specific configuration
type Config struct {
	// Runtime settings
	Socket string `yaml:"socket"`
	Backend string `yaml:"backend"`

	// Image settings
	Registry   string `yaml:"registry"`
	Repository string `yaml:"repository"`
	Tag        string `yaml:"tag"`
}

// GetConfig returns CRI configuration from global YAML config
func GetConfig() *Config {
	yamlCfg := config.GetYAMLConfig()
	langSettings := yamlCfg.Languages["python"] // Default to python for CRI
	
	return &Config{
		Socket:     yamlCfg.Runtime.CRISocket,
		Backend:    yamlCfg.Runtime.Backend,
		Registry:   yamlCfg.Runtime.ImageRegistry,
		Repository: langSettings.Repository,
		Tag:        langSettings.Tag,
	}
}

// ImageRef represents a container image reference parts
type ImageRef struct {
	Registry   string
	Repository string
	Tag        string
}

// ImageRefFor returns the image reference for a given language
func (c *Config) ImageRefFor(lang string) ImageRef {
	registry := c.Registry
	if registry == "" {
		registry = "docker.io"
	}

	yamlCfg := config.GetYAMLConfig()
	langSettings, ok := yamlCfg.Languages[lang]
	if !ok {
		langSettings = yamlCfg.Languages["python"] // Fallback to python
	}

	repo := langSettings.Repository
	if repo == "" {
		repo = "sandbox-python"
	}

	tag := langSettings.Tag
	if tag == "" {
		tag = "latest"
	}

	return ImageRef{
		Registry:   registry,
		Repository: repo,
		Tag:        tag,
	}
}

// ImageFor returns the full image reference string
func (c *Config) ImageFor(lang string) string {
	ref := c.ImageRefFor(lang)
	return ref.Registry + "/" + ref.Repository + ":" + ref.Tag
}

// RegistryAuthInfo holds credentials for registry authentication
type RegistryAuthInfo struct {
	Username      string
	Password      string
	Auth          string
	IdentityToken string
	ServerAddress string
}

// RegistryAuthFor returns registry auth info for the given server
func (c *Config) RegistryAuthFor(server string) RegistryAuthInfo {
	return RegistryAuthInfo{
		Username:      "", // CRI doesn't use username/password auth directly
		Password:      "",
		Auth:          "",
		IdentityToken: "",
		ServerAddress: server,
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