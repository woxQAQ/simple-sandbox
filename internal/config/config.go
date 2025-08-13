package config

import (
	"errors"
	"io/fs"
	"os"

	"gopkg.in/yaml.v3"
)

// RuntimeConfig holds all runtime environment configurations
type RuntimeConfig struct {
	Backend        string `yaml:"backend"`
	MaxConcurrency int    `yaml:"max_concurrency"`
	MaxQueue       int    `yaml:"max_queue"`
	ImageRegistry  string `yaml:"image_registry"`

	// Registry authentication
	RegistryUsername      string `yaml:"registry_username"`
	RegistryPassword      string `yaml:"registry_password"`
	RegistryAuth          string `yaml:"registry_auth"`
	RegistryIdentityToken string `yaml:"registry_identity_token"`

	// Kubernetes settings
	K8sImagePullSecret string `yaml:"k8s_image_pull_secret"`
}

// YAML Configuration structures
type SeccompLangConfig struct {
	K8sMode         string `yaml:"k8s_mode"`
	K8sLocalhostRef string `yaml:"k8s_localhost_ref"`
}

type LanguageSettings struct {
	Repository string            `yaml:"repository"`
	Tag        string            `yaml:"tag"`
	Registry   string            `yaml:"registry"`
	Seccomp    SeccompLangConfig `yaml:"seccomp"`
}

// SandboxConfig holds all YAML-based application configurations
type SandboxConfig struct {
	Runtime   RuntimeConfig               `yaml:"runtime"`
	Languages map[string]LanguageSettings `yaml:"languages"`
}

var yamlConfig *SandboxConfig

// Init loads YAML config from SANDBOX_CONFIG path or default "sandbox.yaml" in CWD.
func Init() error {
	path := os.Getenv("SANDBOX_CONFIG")
	if path == "" {
		path = "sandbox.yaml"
	}

	data, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, fs.ErrNotExist) {
			yamlConfig = &SandboxConfig{
				Runtime:   RuntimeConfig{},
				Languages: map[string]LanguageSettings{},
			}
			return nil
		}
		return err
	}

	var cfg SandboxConfig
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return err
	}

	if cfg.Languages == nil {
		cfg.Languages = map[string]LanguageSettings{}
	}

	yamlConfig = &cfg
	return nil
}

// GetYAMLConfig returns the loaded YAML configuration
func GetYAMLConfig() *SandboxConfig {
	if yamlConfig == nil {
		return &SandboxConfig{
			Runtime:   RuntimeConfig{},
			Languages: map[string]LanguageSettings{},
		}
	}
	return yamlConfig
}
